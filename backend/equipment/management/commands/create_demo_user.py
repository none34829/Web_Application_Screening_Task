from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates or updates a demo user for quickly testing the API."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo", help="Username for the demo user.")
        parser.add_argument(
            "--password",
            default="demo123",
            help="Password for the demo user (use only for local development).",
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        user_model = get_user_model()

        user, created = user_model.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}'."))
        else:
            self.stdout.write(self.style.WARNING(f"Updated password for '{username}'."))
