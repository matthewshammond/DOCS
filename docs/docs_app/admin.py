from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from .models import Invitation
from django.conf import settings


class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "invited_at", "accepted", "send_invitation")

    def send_invitation(self, obj):
        # Check if the invitation has been accepted
        if not obj.accepted:
            invite_link = f"{settings.SITE_URL}/register/{obj.token}"
            send_mail(
                "You are invited to join DOCS",
                f"Use this link to register: {invite_link}",
                settings.DEFAULT_FROM_EMAIL,
                [obj.email],
                fail_silently=False,
            )
            return format_html("<span style='color:green;'>Invitation sent</span>")
        else:
            return format_html(
                "<span style='color:red;'>User already accepted the invitation</span>"
            )

    # Disable adding new invitations through the admin form
    def has_add_permission(self, request):
        return True  # Enable if you want admin to add invites via admin, else change to False


admin.site.register(Invitation, InvitationAdmin)
