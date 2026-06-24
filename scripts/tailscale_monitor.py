#!/usr/bin/env python3
"""
Tailscale Health Monitor for State Electric Office Computer
Checks:
1. Tailscale is connected
2. App (Railway) is reachable
3. File sync folders are accessible

Runs every hour via cron. Reports failures.
"""
import subprocess
import json
import os
import sys
from datetime import datetime

RAILWAY_URL = os.environ.get('RAILWAY_URL', 'https://your-app.up.railway.app')
TAILSCALE_CHECK_IP = '100.64.0.1'  # Tailscale coordinator
SYNC_FOLDERS = os.environ.get('SYNC_FOLDERS', '/home/state/Documents').split(':')


def check_tailscale():
    """Check if Tailscale is connected."""
    try:
        result = subprocess.run(
            ['tailscale', 'status'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and 'Running' in result.stdout:
            return True, "Tailscale connected"
        return False, f"Tailscale not running: {result.stderr[:200]}"
    except Exception as e:
        return False, f"Tailscale check failed: {e}"


def check_railway_app():
    """Check if the Railway app is reachable through Tailscale."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             '--connect-timeout', '10', f'{RAILWAY_URL}/api/health/'],
            capture_output=True, text=True, timeout=15
        )
        code = result.stdout.strip()
        if code == '200':
            return True, f"App reachable (HTTP {code})"
        return False, f"App unreachable (HTTP {code})"
    except Exception as e:
        return False, f"App check failed: {e}"


def check_sync_folders():
    """Check if business document folders are accessible."""
    results = []
    for folder in SYNC_FOLDERS:
        if not folder.strip():
            continue
        exists = os.path.isdir(folder)
        count = len(os.listdir(folder)) if exists else 0
        results.append((folder, exists, count))
    return results


def main():
    timestamp = datetime.now().isoformat()
    report = {
        'timestamp': timestamp,
        'checks': {}
    }
    all_ok = True

    # Check Tailscale
    ok, msg = check_tailscale()
    report['checks']['tailscale'] = {'ok': ok, 'message': msg}
    if not ok:
        all_ok = False

    # Check Railway app
    ok, msg = check_railway_app()
    report['checks']['railway_app'] = {'ok': ok, 'message': msg}
    if not ok:
        all_ok = False

    # Check sync folders
    folder_results = check_sync_folders()
    report['checks']['sync_folders'] = []
    for folder, exists, count in folder_results:
        report['checks']['sync_folders'].append({
            'folder': folder,
            'ok': exists,
            'file_count': count,
        })
        if not exists:
            all_ok = False

    report['overall'] = 'OK' if all_ok else 'FAILURES DETECTED'

    # Write local log
    log_dir = os.path.expanduser('~/.state-electric-monitor')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"health_{datetime.now().strftime('%Y%m%d')}.json")
    with open(log_file, 'a') as f:
        f.write(json.dumps(report) + '\n')

    # Print result (for Mingo to pick up)
    print(json.dumps(report, indent=2))
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
