import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Roles(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    USER = 'USER', 'User'
    VENDOR = 'VENDOR', 'Vendor'

class User(AbstractUser):
    # Keep username for simplicity; you can login by username or email
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.USER)
    email_verified = models.BooleanField(default=False)

    # New signups (USER/VENDOR) must verify email before login
    def save(self, *args, **kwargs):
        if not self.pk and self.role in {Roles.USER, Roles.VENDOR}:
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    EXPIRY_HOURS = 24

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=self.EXPIRY_HOURS)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
