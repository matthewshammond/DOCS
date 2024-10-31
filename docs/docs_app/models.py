from django.db import models
from django.core.validators import RegexValidator
import uuid
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_groups(sender, **kwargs):
    """Create default groups if they don't exist"""
    # Create Float Pilots group
    float_pilots_group, created = Group.objects.get_or_create(name="Float_Pilots")
    if created:
        print("Created Float_Pilots group")

    # Create Admin group
    admin_group, created = Group.objects.get_or_create(name="Admin")
    if created:
        print("Created Admin group")

# Connect the signal to post_migrate
post_migrate.connect(create_default_groups)

class Hospital(models.Model):
    hospital_id = models.CharField(
        max_length=5,
        primary_key=True,
        validators=[
            RegexValidator(
                regex="^[A-Za-z0-9]{3,5}$",
                message="Hospital ID must be 3-5 characters, capital letters and/or numbers.",
            )
        ],
    )
    hospital_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex="^[A-Za-z0-9 -]+$",
                message="Hospital name can only contain letters and numbers.",
            )
        ],
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[A-Za-z ]*$",
                message="City name can only contain letters."
            )
        ],
    )
    state = models.CharField(
        max_length=2,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[A-Za-z]{0,2}$",
                message="State must be 2 capital letters or empty."
            )
        ],
    )
    latitude = models.CharField(max_length=11)
    longitude = models.CharField(max_length=12)
    faa_identifier = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex="^[A-Za-z0-9 ]*$",
                message="FAA Identifier can only contain capital letters and numbers.",
            )
        ],
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    airport = models.BooleanField()
    program = models.ForeignKey('ProgramInfo', on_delete=models.CASCADE, related_name='hospitals')

    def save(self, *args, **kwargs):
        if not self.airport:
            self.faa_identifier = ""  # Make FAA identifier blank when airport is False
        if self.faa_identifier:
            self.faa_identifier = self.faa_identifier.upper()
        if self.hospital_id:
            self.hospital_id = self.hospital_id.upper()
        if self.state:
            self.state = self.state.upper()
        super(Hospital, self).save(*args, **kwargs)

    def __str__(self):
        return self.hospital_name


class ProgramInfo(models.Model):
    program_name = models.CharField(max_length=100)
    program_code = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.program_name} ({self.program_code})"

@receiver(post_save, sender=ProgramInfo)
def create_program_group(sender, instance, created, **kwargs):
    if created:
        Group.objects.create(name=instance.program_code)

@receiver(post_delete, sender=ProgramInfo)
def delete_program_group(sender, instance, **kwargs):
    Group.objects.filter(name=instance.program_code).delete()

# Create Float Pilots group if it doesn't exist
def create_float_pilots_group():
    Group.objects.get_or_create(name="Float_Pilots")


class Invitation(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group)

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def get_display_name(self):
        if self.user.first_name:
            return self.user.first_name
        elif self.user.username == 'leadpilot':
            return 'Lead Pilot'
        return self.user.username

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
