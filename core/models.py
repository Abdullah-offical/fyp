from django.db import models

class ContactMessage(models.Model):
    PAGE_CHOICES = [
        ("home", "Home"),
        ("contact", "Contact"),
    ]
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, default="contact")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} from {self.name} ({self.email})"
