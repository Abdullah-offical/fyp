from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .forms import RegisterForm, LoginForm
from .models import EmailVerificationToken, User, Roles

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

            # ----- ROLE-BASED REDIRECT -----
            if user.is_superuser or user.role == "ADMIN":
                return redirect('accounts:dashboard')   # admin dashboard

            elif user.role == "VENDOR":
                return redirect('accounts:dashboard')   # vendor dashboard

            else:
                # Normal USER
                return redirect('core:home')   # go to home page
            # --------------------------------

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
