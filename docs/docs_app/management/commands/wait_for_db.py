import time
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """Django command to wait for database and create a superuser if not exists."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database...")
        db_up = False
        while not db_up:
            try:
                self.check(databases=["default"])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))

        # Run migrations before creating the superuser
        self.stdout.write("Applying migrations...")
        call_command("migrate")
        self.stdout.write(self.style.SUCCESS("Migrations applied successfully."))

        # Check and create superuser
        self.create_superuser()

    def create_superuser(self):
        """Check if the superuser exists and create if not."""
        User = get_user_model()

        # Set credentials for superuser
        username = "leadpilot"
        password = "password"
        email = ""

        # Check if the superuser already exists
        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating superuser '{username}'...")
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' created successfully!")
            )
        else:
            self.stdout.write(f"Superuser '{username}' already exists.")
