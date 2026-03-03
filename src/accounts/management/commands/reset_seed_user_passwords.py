from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

SEED_PASSWORD = "Test@123"


class Command(BaseCommand):
    help = "Reset all non-superuser account passwords to the seed value (Test@123)."

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(is_superuser=False)
        count = 0
        for user in users:
            user.set_password(SEED_PASSWORD)
            user.save(update_fields=["password"])
            count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Reset passwords for {count} user(s).")
        )
