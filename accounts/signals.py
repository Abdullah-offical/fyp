# accounts/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from core.utils.login_activity import send_login_activity_email

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    try:
        send_login_activity_email(user, request)
    except Exception:
        # Never break login if email runs into trouble
        pass
