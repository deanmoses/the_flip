from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tickets.models import Maintainer
import csv
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Import maintainers from legacy CSV data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing non-superuser users and maintainers before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            # Delete existing non-superuser users and their maintainer profiles
            maintainer_count = Maintainer.objects.exclude(user__is_superuser=True).count()
            user_count = User.objects.filter(is_superuser=False).count()
            Maintainer.objects.exclude(user__is_superuser=True).delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(
                self.style.WARNING(
                    f'Deleted {user_count} non-superuser user(s), {maintainer_count} maintainer profile(s)'
                )
            )

        # Read CSV file
        csv_path = os.path.join(
            os.path.dirname(__file__),
            '../../../..',
            'docs/legacy_data/Maintainers.csv'
        )

        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found at {csv_path}')
            )
            return

        created_admins = 0
        created_maintainers = 0
        existing_users = 0

        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                # Extract data from CSV
                username_from_csv = row.get('Username', '').strip()
                is_admin = row.get('Is Admin', '').strip().upper() == 'TRUE'
                first_name = row.get('First Name', '').strip()
                last_name = row.get('Last Name', '').strip()
                email = row.get('Email', '').strip()
                nickname = row.get('Nickname', '').strip()

                # Generate username if not provided (lowercase first name)
                if username_from_csv:
                    username = username_from_csv
                elif first_name:
                    username = first_name.lower()
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row with no username or first name: {row}')
                    )
                    continue

                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    existing_users += 1
                    self.stdout.write(f'  User "{username}" already exists, skipping')
                    continue

                # Create user (superuser for admins, regular user for maintainers)
                if is_admin:
                    user = User.objects.create_superuser(
                        username=username,
                        email=email if email else '',
                        password='test123',
                        first_name=first_name,
                        last_name=last_name
                    )
                    created_admins += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created admin user: {username} ({first_name} {last_name})')
                    )
                else:
                    user = User.objects.create_user(
                        username=username,
                        email=email if email else '',
                        password='test123',
                        first_name=first_name,
                        last_name=last_name
                    )
                    created_maintainers += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created maintainer: {username} ({first_name} {last_name})')
                    )

                # Create Maintainer profile for all users
                Maintainer.objects.create(
                    user=user,
                    phone='',
                    is_active=True,
                    nickname=nickname
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete: {created_admins} admin(s), {created_maintainers} maintainer(s) created, '
                f'{existing_users} already existed'
            )
        )
