from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Create default admin superuser"

    def handle(self, *args, **kwargs):
        from apps.accounts.models import User
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@betplatform.com", "Admin1234!")
            self.stdout.write(self.style.SUCCESS("Superuser created: admin / Admin1234!"))
        else:
            self.stdout.write("Superuser already exists")
