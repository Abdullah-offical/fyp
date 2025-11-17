from django.urls import path
from . import views

app_name = 'accounts'  # <-- REQUIRED when you use namespace in include()

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uuid:token>/', views.verify_email_view, name='verify'),
    path('resend/', views.resend_verification_view, name='resend'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path("billing/", views.billing_portal, name="billing"),
    path("billing/create-checkout-session/", views.create_checkout_session, name="create_checkout_session"),
    path("stripe-webhook/", views.stripe_webhook, name="stripe_webhook"),
]
