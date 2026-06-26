"""
Upload business documents to cloud storage and create database records.
Run: python manage.py upload_documents
"""
import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from files.models import BusinessDocument


class Command(BaseCommand):
    help = 'Upload business documents from recovery data'

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', type=str, default=None)
        parser.add_argument('--limit', type=int, default=100, help='Max files to upload per run')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        data_dir = options['data_dir'] or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'state-electric-data'
        )
        catalog_file = os.path.join(data_dir, 'document_catalog.json')
        limit = options['limit']
        dry_run = options['dry_run']

        if not os.path.exists(catalog_file):
            self.stdout.write(self.style.ERROR(f'Catalog not found: {catalog_file}'))
            return

        with open(catalog_file, 'r') as f:
            catalog = json.load(f)

        documents = catalog.get('documents', [])[:limit]
        self.stdout.write(f'Processing {len(documents)} of {catalog["total_files"]} documents...')

        uploaded = 0
        skipped = 0
        for doc in documents:
            filepath = os.path.join(data_dir, 'customer-data-recovery', doc['path'])
            if not os.path.exists(filepath):
                skipped += 1
                continue

            if not dry_run:
                # Check if already uploaded
                if BusinessDocument.objects.filter(title=doc['filename'], folder=doc['path']).exists():
                    skipped += 1
                    continue

                try:
                    with open(filepath, 'rb') as f:
                        bd = BusinessDocument(
                            title=doc['filename'],
                            category=doc['category'],
                            folder=doc['path'],
                            description=f"Imported from OneDrive recovery ({doc['type']})",
                        )
                        bd.file.save(doc['filename'], f)
                        bd.save()
                        uploaded += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Failed: {doc["filename"]}: {e}'))
                    skipped += 1
            else:
                uploaded += 1

        self.stdout.write(self.style.SUCCESS(f'Uploaded: {uploaded}, Skipped: {skipped}'))
