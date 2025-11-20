from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime

from .forms import RegisterForm, LoginForm
from .models import EmailVerificationToken, User, Roles


# payment
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Subscription
from django.contrib.auth.decorators import login_required


def _send_verification_email(request, user: User):
    token = EmailVerificationToken.objects.create(user=user)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify', args=[str(token.token)])
    )
    subject = "Verify your email – FYP"
    message = (
        f"Hello {user.username},\n\n"
        f"Please verify your email to activate your account:\n{verify_url}\n\n"
        f"This link expires in {EmailVerificationToken.EXPIRY_HOURS} hours."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created! Check your email for the verification link.")
            _send_verification_email(request, user)
            return render(request, 'accounts/verification_sent.html', {'email': user.email})
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_email_view(request, token):
    try:
        token_obj = EmailVerificationToken.objects.select_related('user').get(token=token, used=False)
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, "Invalid or already used verification link.")
        return redirect('accounts:login')

    if token_obj.is_expired():
        messages.error(request, "Verification link expired. Please request a new one.")
        return redirect('accounts:resend')

    user = token_obj.user
    user.email_verified = True
    user.is_active = True
    user.save()
    token_obj.used = True
    token_obj.save()
    messages.success(request, "Email verified! You can now log in.")
    return render(request, 'accounts/verify_success.html')

def resend_verification_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
            return redirect('accounts:resend')

        if user.email_verified:
            messages.info(request, "This email is already verified. Please log in.")
            return redirect('accounts:login')

        _send_verification_email(request, user)
        messages.success(request, "Verification email resent. Check your inbox.")
        return render(request, 'accounts/verification_sent.html', {'email': user.email})
    return render(request, 'accounts/resend.html')

# def login_view(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             messages.success(request, f"Welcome, {user.username}!")
#             return redirect('accounts:dashboard')
#     else:
#         form = LoginForm()
#     return render(request, 'accounts/login.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            # Admin
            if user.is_superuser or user.role == "ADMIN":
                return redirect('accounts:dashboard')

            # Vendor
            if user.role == "VENDOR":
                return redirect('accounts:dashboard')

            # Normal user → if no active subscription, go to billing
            sub, _ = Subscription.objects.get_or_create(user=user)
            if sub.status not in ["trialing", "active"]:
                return redirect('accounts:billing')

            return redirect('core:home')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})



def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')

@login_required
def dashboard_view(request):
    # Simple role-based landing
    user = request.user
    if user.is_superuser or user.role == Roles.ADMIN:
        role_msg = "Admin Dashboard"
    elif user.role == Roles.VENDOR:
        role_msg = "Vendor Dashboard"
    else:
        role_msg = "User Dashboard"
        
    return render(request, 'accounts/dashboard.html', {'role_msg': role_msg})


# # paymrnts

# stripe.api_key = settings.STRIPE_SECRET_KEY

# @login_required
# def billing_portal(request):
#     # try to get or create subscription row
#     sub, created = Subscription.objects.get_or_create(user=request.user)

#     context = {
#         "subscription": sub,
#         "stripe_pk": settings.STRIPE_PUBLISHABLE_KEY,
#     }
#     return render(request, "accounts/billing.html", context)


# @login_required
# def create_checkout_session(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST only"}, status=405)

#     sub, created = Subscription.objects.get_or_create(user=request.user)

#     # Create or reuse Stripe customer
#     if sub.stripe_customer_id:
#         customer_id = sub.stripe_customer_id
#     else:
#         customer = stripe.Customer.create(
#             email=request.user.email or None,
#             name=request.user.username,
#         )
#         customer_id = customer.id
#         sub.stripe_customer_id = customer_id
#         sub.save(update_fields=["stripe_customer_id"])

#     # One-time $1 verification charge in TEST MODE
#     stripe.PaymentIntent.create(
#         amount=100,             # $1.00
#         currency="usd",
#         customer=customer_id,
#         description="Card verification charge (test mode)",
#         payment_method_types=["card"],
#     )

#     # Subscription checkout (with 30-day trial defined in Price)
#     checkout_session = stripe.checkout.Session.create(
#         customer=customer_id,
#         success_url=request.build_absolute_uri(reverse("accounts:billing")) + "?session_id={CHECKOUT_SESSION_ID}",
#         cancel_url=request.build_absolute_uri(reverse("accounts:billing")),
#         mode="subscription",
#         line_items=[{
#             "price": settings.STRIPE_PRICE_ID,
#             "quantity": 1,
#         }],
#     )

#     return JsonResponse({"id": checkout_session.id})


# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
#     endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except ValueError:
#         return HttpResponse(status=400)
#     except stripe.error.SignatureVerificationError:
#         return HttpResponse(status=400)

#     # Handle subscription events
#     if event["type"] in ["customer.subscription.updated", "customer.subscription.created"]:
#         sub_data = event["data"]["object"]
#         stripe_sub_id = sub_data["id"]
#         status = sub_data["status"]
#         current_period_end = sub_data["current_period_end"]

#         try:
#             sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
#         except Subscription.DoesNotExist:
#             # maybe first time – try to attach by customer id
#             customer_id = sub_data["customer"]
#             sub = Subscription.objects.filter(stripe_customer_id=customer_id).first()
#             if sub:
#                 sub.stripe_subscription_id = stripe_sub_id

#         if sub:
#             from datetime import datetime
#             sub.status = status
#             sub.current_period_end = datetime.fromtimestamp(current_period_end)
#             sub.save()

#     return HttpResponse(status=200)



stripe.api_key = settings.STRIPE_SECRET_KEY
# ----------------- BILLING PAGE -----------------
@login_required
def billing_portal(request):
    # Make sure every user has a subscription row
    sub, created = Subscription.objects.get_or_create(user=request.user)

    context = {
        "subscription": sub,
        "stripe_pk": settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, "accounts/billing.html", context)


# ----------------- CREATE CHECKOUT SESSION -----------------
@login_required
def create_checkout_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # 1. Get or create local subscription row
    sub, created = Subscription.objects.get_or_create(user=request.user)

    # 2. Get or create Stripe customer
    if sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer = stripe.Customer.create(
            email=request.user.email or None,
            name=request.user.username,
        )
        customer_id = customer.id
        sub.stripe_customer_id = customer_id
        sub.save(update_fields=["stripe_customer_id"])

    # ⚠️ OPTIONAL: you can remove this block entirely if you don’t
    # really need the extra $1 verification.
    #
    # stripe.PaymentIntent.create(
    #     amount=100,  # $1.00
    #     currency="usd",
    #     customer=customer_id,
    #     description="Card verification charge (test mode)",
    #     payment_method_types=["card"],
    # )

    # 3. Create Subscription Checkout Session (Price has 1-month trial)
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": settings.STRIPE_PRICE_ID,
            "quantity": 1,
        }],
        success_url=(
            request.build_absolute_uri(reverse("accounts:billing"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=request.build_absolute_uri(reverse("accounts:billing")),
    )

    return JsonResponse({"id": checkout_session.id})


# ----------------- STRIPE WEBHOOK -----------------
# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
#     endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except (ValueError, stripe.error.SignatureVerificationError):
#         # Invalid payload OR invalid signature
#         return HttpResponse(status=400)

#     # --- 1. When checkout is successful for the first time ---
#     if event["type"] == "checkout.session.completed":
#         session = event["data"]["object"]

#         customer_id = session.get("customer")
#         stripe_sub_id = session.get("subscription")
#         if not (customer_id and stripe_sub_id):
#             return HttpResponse(status=200)

#         # Find our local Subscription row by customer id
#         sub = Subscription.objects.filter(
#             stripe_customer_id=customer_id
#         ).first()
#         if not sub:
#             return HttpResponse(status=200)

#         # Fetch full subscription from Stripe to get status + period end
#         stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)

#         from datetime import datetime

#         sub.stripe_subscription_id = stripe_sub_id
#         sub.status = stripe_sub["status"]          # active, trialing, etc.
#         sub.current_period_end = datetime.fromtimestamp(
#             stripe_sub["current_period_end"]
#         )
#         sub.save()

#     # --- 2. Later updates (renew, cancel, etc.) ---
#     elif event["type"] in [
#         "customer.subscription.updated",
#         "customer.subscription.deleted",
#     ]:
#         stripe_sub = event["data"]["object"]
#         stripe_sub_id = stripe_sub["id"]

#         try:
#             sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
#         except Subscription.DoesNotExist:
#             return HttpResponse(status=200)

#         from datetime import datetime

#         sub.status = stripe_sub["status"]
#         if stripe_sub.get("current_period_end"):
#             sub.current_period_end = datetime.fromtimestamp(
#                 stripe_sub["current_period_end"]
#             )
#         sub.save()

#     return HttpResponse(status=200)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        # invalid payload or signature
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    # helper: find our Subscription row & update it
    def update_subscription(stripe_customer_id=None,
                            stripe_subscription_id=None,
                            status=None,
                            current_period_end=None):
        sub = None

        # 1) try by subscription id
        if stripe_subscription_id:
            sub = Subscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).first()

        # 2) if not found, try by customer id
        if not sub and stripe_customer_id:
            sub = Subscription.objects.filter(
                stripe_customer_id=stripe_customer_id
            ).first()
            # first time: attach the subscription id
            if sub and stripe_subscription_id and not sub.stripe_subscription_id:
                sub.stripe_subscription_id = stripe_subscription_id

        if not sub:
            return  # nothing to update

        if status:
            sub.status = status
        if current_period_end:
            sub.current_period_end = datetime.fromtimestamp(current_period_end)

        sub.save()

    # ---- handle events ----

    # When Stripe creates or updates the subscription
    if event_type in ("customer.subscription.created",
                      "customer.subscription.updated"):
        update_subscription(
            stripe_customer_id=data["customer"],
            stripe_subscription_id=data["id"],
            status=data["status"],
            current_period_end=data["current_period_end"],
        )

    # When Checkout finishes successfully
    elif event_type == "checkout.session.completed":
        update_subscription(
            stripe_customer_id=data.get("customer"),
            stripe_subscription_id=data.get("subscription"),
        )

    # you can log other event types if you want, but not required
    return HttpResponse(status=200)