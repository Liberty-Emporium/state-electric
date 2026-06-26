"""
Scan and catalog all business documents for import.
Run: python manage.py catalog_documents
"""
import os
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Catalog all business documents from the recovery data'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default='state-electric-data/customer-data-recovery')
        parser.add_argument('--output', type=str, default='state-electric-data/document_catalog.json')

    def handle(self, *args, **options):
        source = options['source']
        output = options['output']

        skip_extensions = {'.exe', '.iso', '.dll', '.sys', '.msi', '.bat', '.cmd', '.ps1',
                          '.tmp', '.temp', '.log', '.dat', '.db', '.cab', '.inf', '.drv',
                          '.ocx', '.scr', '.com', '.cpl', '.hta', '.jse', '.vbs', '.vbe',
                          '.wsf', '.wsh', '.reg', '.ini', '.download', '.hyb', '.ins', '.pup'}
        
        skip_paths = ['AppData', 'ProgramData', 'System Volume Information', '$Recycle.Bin',
                     'Windows', 'Temp', 'tmp', 'Staging', '.Trash-10000', 'MicrosoftEdgeBackups',
                     'Edge Wallet', 'Edge Shopping', 'Network_Driver', 'HPQWare']

        business_extensions = {'.xlsx', '.xls', '.csv', '.pdf', '.docx', '.doc',
                              '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif',
                              '.msg', '.eml', '.html', '.htm', '.mhtml',
                              '.txt', '.md', '.rtf', '.zip', '.7z', '.rar'}

        catalog = []
        total_size = 0
        skipped = 0

        for root, dirs, files in os.walk(source):
            dirs[:] = [d for d in dirs if d not in skip_paths and not d.startswith('$')]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in skip_extensions:
                    skipped += 1
                    continue
                if any(sp in filepath for sp in skip_paths):
                    skipped += 1
                    continue
                if ext not in business_extensions:
                    skipped += 1
                    continue
                
                try:
                    size = os.path.getsize(filepath)
                except:
                    size = 0
                
                rel_path = os.path.relpath(filepath, source)
                total_size += size
                
                # Determine category from path
                category = 'other'
                if 'OneDrive' in rel_path or 'Desktop' in rel_path or 'Documents' in rel_path:
                    if ext in ('.xlsx', '.xls', '.csv'):
                        category = 'spreadsheet'
                    elif ext == '.pdf':
                        category = 'document'
                    elif ext in ('.docx', '.doc', '.txt', '.rtf'):
                        category = 'document'
                    elif ext in ('.jpg', '.jpeg', '.png', '.tiff', '.tif'):
                        category = 'scan'
                    elif ext in ('.msg', '.eml'):
                        category = 'email'
                    elif ext == '.zip':
                        category = 'archive'
                
                catalog.append({
                    'path': rel_path,
                    'filename': filename,
                    'size': size,
                    'type': ext,
                    'category': category,
                })

        result = {
            'total_files': len(catalog),
            'total_size_mb': round(total_size / (1024 * 1024), 1),
            'skipped': skipped,
            'documents': catalog,
        }

        with open(output, 'w') as f:
            json.dump(result, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Catalog complete:'))
        self.stdout.write(f'  Business files: {len(catalog)}')
        self.stdout.write(f'  Total size: {total_size / (1024*1024):.1f} MB')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Saved to: {output}')
