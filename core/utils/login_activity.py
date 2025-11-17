# core/utils/login_activity.py
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

def get_client_ip(request):
    """Best-effort public IP detection (works behind ngrok/reverse proxies)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # X-Forwarded-For: client, proxy1, proxy2...
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

def get_city_from_ip(ip):
    """Try GeoIP lookup. Falls back to 'Unknown City'."""
    try:
        from geoip2.database import Reader
        import os
        db_path = getattr(settings, "GEOIP_PATH", None)
        if not db_path:
            return "Unknown City"
        city_db = os.path.join(db_path, "GeoLite2-City.mmdb")
        if not os.path.exists(city_db):
            return "Unknown City"
        reader = Reader(city_db)
        resp = reader.city(ip)
        city = resp.city.name or ""
        country = resp.country.name or ""
        reader.close()
        label = ", ".join([x for x in [city, country] if x])
        return label or "Unknown City"
    except Exception:
        return "Unknown City"

def parse_user_agent(ua_string):
    """Parse UA into (device, browser). Falls back to raw pieces if lib missing."""
    if not ua_string:
        return ("Unknown Device", "Unknown Browser")
    try:
        from user_agents import parse
        ua = parse(ua_string)
        device = "Mobile" if ua.is_mobile else "Tablet" if ua.is_tablet else "PC" if ua.is_pc else "Bot" if ua.is_bot else "Unknown Device"
        browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
        return (device, browser or "Unknown Browser")
    except Exception:
        # Very rough fallback
        browser_guess = "Unknown Browser"
        for key in ["Chrome", "Firefox", "Safari", "Edge", "Opera", "MSIE"]:
            if key in ua_string:
                browser_guess = key
                break
        device_guess = "Mobile" if "Mobi" in ua_string else "PC"
        return (device_guess, browser_guess)

def send_login_activity_email(user, request):
    """Send email to the user and to ADMIN with login info."""
    ip = get_client_ip(request)
    city = get_city_from_ip(ip)
    device, browser = parse_user_agent(request.META.get("HTTP_USER_AGENT", ""))

    when = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    subject = f"New login to your account"
    message = (
        f"Hello {getattr(user, 'first_name', '') or user.username},\n\n"
        f"A login to your account just occurred.\n\n"
        f"• City: {city}\n"
        f"• Device: {device}\n"
        f"• Browser: {browser}\n"
        f"• IP: {ip or 'Unknown'}\n"
        f"• Time: {when}\n\n"
        f"If this was you, you can ignore this email.\n"
        f"If you don't recognize this activity, please reset your password.\n\n"
        f"— BlueprintPro"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@fyp.local")
    recipients = [addr for addr in [user.email, getattr(settings, "LOGIN_ACTIVITY_ADMIN_EMAIL", None)] if addr]
    if not recipients:
        return  # nothing to send to

    send_mail(
    subject=subject,
    message=message,
    from_email=from_email,
    recipient_list=recipients,
    fail_silently=True,
)
