from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Q

from django.core.paginator import Paginator
from blueprints.models import PlotBlueprint, BlueprintStatus
from accounts.models import Roles


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import Roles
from blueprints.models import PlotBlueprint, BlueprintStatus
from .forms import ContactForm
from .models import ContactMessage

User = get_user_model()

def _handle_contact_post(request, page_label: str):
    """Validate, save, email; returns True if handled (and redirected)."""
    if request.method != "POST":
        return False

    form = ContactForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please fix the errors and submit again.")
        return False

    cd = form.cleaned_data
    # Save to DB
    ContactMessage.objects.create(
        name=cd["name"],
        email=cd["email"],
        subject=cd["subject"],
        message=cd["message"],
        page=page_label,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    # Email to you
    try:
        send_mail(
            subject=f"[Contact:{page_label}] {cd['subject']}",
            message=(
                f"Name: {cd['name']}\n"
                f"Email: {cd['email']}\n"
                f"Page: {page_label}\n"
                f"IP: {request.META.get('REMOTE_ADDR')}\n\n"
                f"Message:\n{cd['message']}"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@fyp.local"),
            recipient_list=["aj161474@gmail.com"],
            fail_silently=False,
        )
    except Exception as e:
        # Still succeed UX-wise, but tell in admin logs/console
        messages.warning(request, f"Saved message, but email failed: {e}")

    messages.success(request, "Thanks! Your message has been sent.")
    return True

def home(request):
    # Handle contact form POST on the home page
    if _handle_contact_post(request, page_label="home"):
        return redirect("core:home")

    # Featured (admin uploads only)
    admin_filter = Q(owner__is_superuser=True) | Q(owner__role=Roles.ADMIN)
    featured_blueprints = (
        PlotBlueprint.objects
        .filter(admin_filter, status=BlueprintStatus.APPROVED)
        .select_related("owner")
        .order_by("-created_at")[:6]
    )

    # Counters
    generated_blueprints = PlotBlueprint.objects.filter(status=BlueprintStatus.APPROVED).count()
    vendors_count = User.objects.filter(role=Roles.VENDOR).count()
    users_count = User.objects.filter(role=Roles.USER).count()

    # Blank contact form for the home page section
    form = ContactForm()

    return render(request, "core/home.html", {
        "featured_blueprints": featured_blueprints,
        "generated_blueprints": generated_blueprints,
        "vendors_count": vendors_count,
        "users_count": users_count,
        "contact_form": form,
    })

def contact(request):
    if _handle_contact_post(request, page_label="contact"):
        return redirect("core:contact")
    return render(request, "core/contact.html", {"contact_form": ContactForm()})




# User = get_user_model()

# def home(request):
#     # ---- Featured (only admin-uploaded, approved, max 6) ----
#     admin_filter = Q(owner__is_superuser=True) | Q(owner__role=Roles.ADMIN)
#     featured_blueprints = (
#         PlotBlueprint.objects
#         .filter(admin_filter, status=BlueprintStatus.APPROVED)
#         .select_related("owner")
#         .order_by("-created_at")[:6]
#     )

#     # ---- Counters ----
#     generated_blueprints = PlotBlueprint.objects.filter(status=BlueprintStatus.APPROVED).count()
#     vendors_count = User.objects.filter(role=Roles.VENDOR).count()
#     users_count = User.objects.filter(role=Roles.USER).count()

#     context = {
#         "featured_blueprints": featured_blueprints,
#         "generated_blueprints": generated_blueprints,
#         "vendors_count": vendors_count,
#         "users_count": users_count,
#     }
#     return render(request, "core/home.html", context)


# def contact(request):
#     return render(request, "core/contact.html")

def generate_blueprint(request):
    return render(request, "core/generate-blueprint.html")

def property_details(request):
    return render(request, "core/property-details.html")

def property_details(request):
    qs = PlotBlueprint.objects.filter(status=BlueprintStatus.APPROVED).select_related("owner").order_by("-created_at")
    paginator = Paginator(qs, 9)  # 9 cards per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "core/property-details.html", {"page_obj": page_obj})


def view_blueprint(request):
    # Static/placeholder page (marketing page)
    return render(request, "core/view-blueprint.html")