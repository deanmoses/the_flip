from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config
from tickets.models import Maintainer
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates default admin users and maintainer profiles if they do not exist'

    def handle(self, *args, **options):
        # Default admin users configuration
        default_admins = [
            {
                "username": "moses",
                "email": "moses@tacocat.com",
                "first_name": "Dean",
                "last_name": "Moses",
                "password": "test123"
            },
            {
                "username": "william",
                "email": "william@theflip.com",
                "first_name": "William",
                "last_name": "Pietri",
                "password": "test123"
            }
        ]

        # Get admin users from environment variable or use defaults
        admin_users_json = config('ADMIN_USERS', default='')
        if admin_users_json:
            try:
                admin_users = json.loads(admin_users_json)
            except json.JSONDecodeError:
                self.stdout.write(
                    self.style.ERROR('Invalid ADMIN_USERS JSON format. Using defaults.')
                )
                admin_users = default_admins
        else:
            admin_users = default_admins

        # Process each admin user
        for admin_data in admin_users:
            username = admin_data.get('username')
            email = admin_data.get('email')
            password = admin_data.get('password')
            first_name = admin_data.get('first_name', '')
            last_name = admin_data.get('last_name', '')

            if not username or not email or not password:
                self.stdout.write(
                    self.style.ERROR(f'Skipping incomplete admin user data: {admin_data}')
                )
                continue

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Admin user "{username}" already exists. Skipping creation.')
                )
                user = User.objects.get(username=username)
            else:
                # Create superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created admin user: {username}')
                )

            # Create Maintainer profile if it doesn't exist
            if not hasattr(user, 'maintainer'):
                Maintainer.objects.create(
                    user=user,
                    phone='',
                    is_active=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created maintainer profile for: {username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Maintainer profile for "{username}" already exists.')
                )

        self.stdout.write(
            self.style.SUCCESS('Admin setup complete!')
        )
