from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

class Command(BaseCommand):
    help = 'Sets up default groups and adds staff users to Admin group'

    def handle(self, *args, **kwargs):
        # Create groups if they don't exist
        float_pilots_group, _ = Group.objects.get_or_create(name="Float_Pilots")
        admin_group, _ = Group.objects.get_or_create(name="Admin")

        # Add all staff users to Admin group
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            if not user.groups.filter(name="Admin").exists():
                admin_group.user_set.add(user)
                self.stdout.write(self.style.SUCCESS(f'Added {user.username} to Admin group'))

        self.stdout.write(self.style.SUCCESS('Successfully set up groups')) 