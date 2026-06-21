"""Seed initial data for State Electric."""
from django.core.management.base import BaseCommand
from core.models import Division, User, Customer, Invoice


class Command(BaseCommand):
    help = 'Seed initial divisions and demo data'

    def handle(self, *args, **options):
        # Create divisions
        commercial, _ = Division.objects.get_or_create(
            name='commercial', defaults={'display_name': 'Commercial Electrical'}
        )
        residential, _ = Division.objects.get_or_create(
            name='residential', defaults={'display_name': 'Residential Electrical'}
        )
        self.stdout.write(self.style.SUCCESS(f'Divisions: {commercial}, {residential}'))

        # Create superuser if not exists
        if not User.objects.filter(username='jay').exists():
            User.objects.create_superuser('jay', 'jay@alexanderai.site', 'password123')
            self.stdout.write(self.style.SUCCESS('Superuser created: jay'))
        else:
            self.stdout.write('Superuser already exists')

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
