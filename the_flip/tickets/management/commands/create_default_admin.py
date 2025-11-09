from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config
from tickets.models import Maintainer

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a default admin user and maintainer profile if they do not exist'

    def handle(self, *args, **options):
        # Get credentials from environment variables with defaults for local dev
        username = config('ADMIN_USERNAME', default='admin')
        email = config('ADMIN_EMAIL', default='admin@theflip.com')
        password = config('ADMIN_PASSWORD', default='changeme123')

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
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user: {username}')
            )

        # Create Maintainer profile if it doesn't exist
        if not hasattr(user, 'maintainer'):
            maintainer = Maintainer.objects.create(
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
