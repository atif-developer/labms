from django.core.management.base import BaseCommand
from accounts.models import User
from tests_mgmt.models import TestCategory, Test
from lab.models import Laboratory


class Command(BaseCommand):
    help = 'Create initial admin user and sample data'

    def handle(self, *args, **options):
        # Create superuser/admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@labms.com',
                password='admin123',
                first_name='System',
                last_name='Admin',
                role=User.ROLE_ADMIN,
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists.')

        # Sample categories
        cats = ['Hematology', 'Biochemistry', 'Microbiology', 'Immunology', 'Radiology']
        for cat_name in cats:
            TestCategory.objects.get_or_create(name=cat_name, defaults={'description': f'{cat_name} tests'})

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('\nTo register a laboratory, visit: /lab/register/')
        self.stdout.write('To register as patient, visit: /accounts/register/')
