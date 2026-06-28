"""
Simple bulk document upload API endpoint.
Deploy this, then POST files to /api/files/bulk-upload/
"""
import os
import sys
import shutil
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/django/state-electric-app')

import django
django.setup()

from django.core.files import File
from files.models import BusinessDocument
from core.models import Customer

USB_PATH = "/run/media/django/Ventoy/customer-data-recovery"
MEDIA_PATH = "/home/django/state-electric-app/media/documents"

CATEGORY_MAP = {
    'invoice': 'invoice', 'invoices': 'invoice',
    'receipt': 'receipt', 'receipts': 'receipt',
    'permit': 'permit', 'permits': 'permit',
    'insurance': 'insurance', 'contract': 'contract',
    'photo': 'photo', 'scans': 'scan', 'scan': 'scan',
    'work order': 'work_order', 'work_order': 'work_order',
    'estimate': 'estimate', 'quote': 'estimate',
    'bank': 'bank_doc', 'tax': 'tax_doc',
}

def get_category_from_path(filepath):
    path_lower = filepath.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in path_lower:
            return category
    return 'other'

def find_customer_match(filename):
    customers = {c.name.lower().strip(): c for c in Customer.objects.all()}
    fname_lower = filename.lower()
    for cust_name, customer in customers.items():
        name_parts = cust_name.split()
        if len(name_parts) >= 2:
            if name_parts[0] in fname_lower and name_parts[-1] in fname_lower:
                return customer
        elif len(name_parts) == 1:
            if name_parts[0] in fname_lower:
                return customer
    return None

def get_folder_name(filepath):
    rel_path = os.path.relpath(filepath, USB_PATH)
    parts = rel_path.split(os.sep)
    if len(parts) >= 2:
        return parts[-2]
    return 'Imported'

def import_documents(dry_run=True):
    doc_extensions = {'.pdf', '.xlsx', '.xls', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.tiff', '.msg', '.csv', '.txt', '.html', '.mhtml', '.eml', '.zip', '.7z'}
    include_folders = ['OneDrive', 'QuickBooks', 'Documents', 'Desktop', 'Downloads', 'Pictures']
    skip_folders = ['AppData', 'ProgramData', 'Windows', 'Program Files', '$Recycle.Bin', 
                    '.Trash-1000', 'MicrosoftEdgeBackups', 'System Volume Information',
                    'node_modules', '__pycache__', '.git', 'HP', 'Dell', 'Adobe',
                    'Microsoft', 'WindowsApps', 'Temp', 'tmp', 'cache', 'Cache',
                    'Local Settings', 'NetHood', 'PrintHood', 'Recent', 'SendTo',
                    'Start Menu', 'Templates', 'Cookies', 'LocalLow']
    
    files_to_import = []
    for root, dirs, files in os.walk(USB_PATH):
        is_user_folder = any(uf in root for uf in include_folders)
        is_skip_folder = any(sf in root for sf in skip_folders)
        if not is_user_folder or is_skip_folder:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in doc_extensions:
                filepath = os.path.join(root, f)
                size = os.path.getsize(filepath)
                if size > 1000:
                    files_to_import.append(filepath)
    
    print(f"Found {len(files_to_import)} files to import")
    
    if dry_run:
        print("DRY RUN - Not importing")
        return
    
    os.makedirs(MEDIA_PATH, exist_ok=True)
    imported = 0
    skipped = 0
    errors = 0
    
    for filepath in files_to_import:
        try:
            filename = os.path.basename(filepath)
            category = get_category_from_path(filepath)
            folder = get_folder_name(filepath)
            customer = find_customer_match(filename)
            
            if BusinessDocument.objects.filter(title=filename, folder=folder).exists():
                skipped += 1
                continue
            
            today = datetime.now()
            dest_dir = os.path.join(MEDIA_PATH, str(today.year), f"{today.month:02d}")
            os.makedirs(dest_dir, exist_ok=True)
            
            name, ext = os.path.splitext(filename)
            dest_filename = f"{name}_{imported:05d}{ext}"
            dest_path = os.path.join(dest_dir, dest_filename)
            
            shutil.copy2(filepath, dest_path)
            
            with open(dest_path, 'rb') as f:
                doc = BusinessDocument(
                    title=filename[:200],
                    category=category,
                    folder=folder,
                    description=f"Imported from USB: {os.path.relpath(filepath, USB_PATH)[:200]}",
                    customer=customer,
                )
                doc.file.save(dest_filename, File(f))
                doc.save()
            
            imported += 1
            if imported % 500 == 0:
                print(f"  Imported {imported} files...")
                
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"  ERROR: {os.path.basename(filepath)}: {e}")
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total in DB: {BusinessDocument.objects.count()}")

if __name__ == '__main__':
    import_documents(dry_run=False)
