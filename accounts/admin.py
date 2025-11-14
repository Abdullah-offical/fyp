from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, EmailVerificationToken

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'email_verified', 'is_staff')
    list_filter = ('role', 'email_verified', 'is_active', 'is_staff', 'is_superuser')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role & Verification', {'fields': ('role', 'email_verified')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used')
    list_filter = ('used',)
