#!/usr/bin/env python3
"""
State Electric - Data Sync Script
Runs on Mingo. Connects to office computer via Tailscale,
pulls any changed business files, and syncs with Railway app.

Usage:
    python3 data_sync.py --once          # single run
    python3 data_sync.py --watch         # watch mode (loops)
    python3 data_sync.py --full          # full backup everything
"""

import os
import subprocess
import json
import hashlib
import sys
import shutil
from datetime import datetime

# Configuration
OFFICE_HOST = os.environ.get('OFFICE_HOST', 'state-office')
OFFICE_USER = os.environ.get('OFFICE_USER', 'state')
OFFICE_FOLDERS = os.environ.get('OFFICE_FOLDERS', '/home/state/Documents').split(':')
LOCAL_BACKUP = os.environ.get('LOCAL_BACKUP', '/home/mingo/state-electric-backup')
SYNC_FILE = os.path.join(LOCAL_BACKUP, 'sync_manifest.json')

# Files to ignore
IGNORE_PATTERNS = ['*.tmp', '*.bak', '~*', '.Trash*', 'Thumbs.db', 'desktop.ini']


def ensure_dirs():
    """Create local backup directories."""
    os.makedirs(LOCAL_BACKUP, exist_ok=True)
    os.makedirs(os.path.join(LOCAL_BACKUP, 'files'), exist_ok=True)
    os.makedirs(os.path.join(LOCAL_BACKUP, 'exports'), exist_ok=True)


def file_hash(filepath):
    """Calculate MD5 hash of a file."""
    h = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def get_office_file_list(folder):
    """Get file list from office computer via SSH/Tailscale."""
    try:
        result = subprocess.run(
            ['ssh', f'{OFFICE_USER}@{OFFICE_HOST}', f'find "{folder}" -type f'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        files = []
        for line in result.stdout.strip().split('\n'):
            filepath = line.strip()
            if not filepath:
                continue
            # Skip ignored patterns
            name = os.path.basename(filepath)
            if any(name.endswith(ext.replace('*', '')) for ext in IGNOR_PATTERNS if '*' in ext):
                continue
            if name.startswith('~') or name.startswith('.'):
                continue
            # Get file hash
            hash_result = subprocess.run(
                ['ssh', f'{OFFICE_USER}@{OFFICE_HOST}', f'md5sum "{filepath}"'],
                capture_output=True, text=True, timeout=15
            )
            md5 = hash_result.stdout.split()[0] if hash_result.returncode == 0 else 'unknown'
            # Get modification time
            stat_result = subprocess.run(
                ['ssh', f'{OFFICE_USER}@{OFFICE_HOST}', f'stat -c %Y "{filepath}"'],
                capture_output=True, text=True, timeout=15
            )
            mtime = stat_result.stdout.strip() if stat_result.returncode == 0 else '0'
            files.append({
                'path': filepath,
                'hash': md5,
                'mtime': int(mtime),
            })
        return files
    except subprocess.TimeoutExpired:
        return None


def pull_file(remote_path, local_path):
    """Pull a file from office computer via rsync over Tailscale."""
    try:
        os.makedirs(local_path.dirname(local_path), exist_ok=True)
        result = subprocess.run(
            ['rsync', '-avz', '--checksum',
             f'{OFFICE_USER}@{OFFICE_HOST}:{remote_path}', str(local_path)],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def run_once(full=False):
    """Run a single sync cycle."""
    ensure_dirs()
    timestamp = datetime.now().isoformat()

    # Load existing manifest
    manifest = {}
    if os.path.exists(SYNC_FILE) and not full:
        with open(SYNC_FILE) as f:
            manifest = json.load(f)

    results = {'timestamp': timestamp, 'files': [], 'errors': []}

    for folder in OFFICE_FOLDERS:
        if not folder.strip():
            continue
        print(f"[sync] Scanning {folder}...", flush=True)

        files = get_office_file_list(folder)
        if files is None:
            results['errors'].append(f"Cannot reach office for {folder}")
            continue

        for f in files:
            rel_path = f['path'].replace(folder.lstrip('/'), '').lstrip('/')
            local_dir = os.path.join(LOCAL_BACKUP, 'files', os.path.dirname(rel_path))

            # Check if file has changed
            prev = manifest.get('files', {}).get(f['path'], {})
            if not full and prev.get('hash') == f['hash']:
                continue  # file unchanged

            from pathlib import Path
            local_path = Path(local_dir) / os.path.basename(f['path'])
            local_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"[sync] Pulling: {rel_path}...", end=' ', flush=True)
            if pull_file(f['path'], str(local_path)):
                print("OK")
                results['files'].append({
                    'path': f['path'],
                    'hash': f['hash'],
                    'size': local_path.stat().st_size if local_path.exists() else 0,
                })
            else:
                print("FAILED")
                results['errors'].append(f"Failed to pull {f['path']}")

    # Save manifest
    manifest = {'last_sync': timestamp, 'files': {}}
    for entry in results['files']:
        manifest['files'][entry['path']] = {'hash': entry['hash']}
    # Keep previous entries
    if os.path.exists(SYNC_FILE):
        try:
            with open(SYNC_FILE) as f:
                old = json.load(f)
                old_files = old.get('files', {})
                for k, v in old_files.items():
                    if k not in manifest['files']:
                        manifest['files'][k] = v
        except:
            pass

    with open(SYNC_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"[sync] Done. {len(results['files'])} updated, {len(results['errors'])} errors.", flush=True)
    return results


if __name__ == '__main__':
    import pathlib

    if '--full' in sys.argv:
        result = run_once(full=True)
    elif '--once' in sys.argv:
        result = run_once(full=False)
    elif '--watch' in sys.argv:
        print("[sync] Starting watch mode (5 min interval)...", flush=True)
        while True:
            result = run_once(full=False)
            if result.get('files'):
                print(f"[sync] {len(result['files'])} changes detected", flush=True)
            import time
            time.sleep(300)
    else:
        result = run_once(full=False)
