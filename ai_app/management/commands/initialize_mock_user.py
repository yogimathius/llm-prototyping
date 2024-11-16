from django.core.management.base import BaseCommand
from ai_app.models import User


class Command(BaseCommand):
    help = "Initialize mock user"

    def handle(self, *args, **kwargs):
        User.objects.create(username="testuser")
        self.stdout.write(self.style.SUCCESS("Mock user created"))
