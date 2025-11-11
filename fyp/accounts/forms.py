from django import forms
from django.contrib.auth import authenticate
from .models import User, Roles

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'role')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow USER or VENDOR from the form
        self.fields['role'].choices = [
            (Roles.USER, 'User'),
            (Roles.VENDOR, 'Vendor'),
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username_or_email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        u = cleaned.get('username_or_email')
        p = cleaned.get('password')
        if u and p:
            # Try username, then email
            self.user_cache = authenticate(username=u, password=p)
            if self.user_cache is None:
                try:
                    user_obj = User.objects.get(email__iexact=u)
                    self.user_cache = authenticate(username=user_obj.username, password=p)
                except User.DoesNotExist:
                    pass
            if self.user_cache is None:
                raise forms.ValidationError("Invalid credentials.")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Account is inactive. Please verify your email.")
        return cleaned

    def get_user(self):
        return self.user_cache
