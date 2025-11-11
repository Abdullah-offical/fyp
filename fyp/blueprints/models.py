
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class BlueprintStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"

def plot_upload_path(instance, filename):
    return f"plots/{instance.owner_id}/{filename}"

class PlotBlueprint(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plot_blueprints")
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to=plot_upload_path, blank=True, null=True)

    # ----- NEW: searchable plot size -----
    class Units(models.TextChoices):
        FEET = "ft", "Feet"
        METER = "m", "Meter"

    plot_width  = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    plot_height = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    plot_unit   = models.CharField(max_length=2, choices=Units.choices, blank=True, default=Units.FEET)
    # -------------------------------------

    # Bedrooms (1–5) sizes (all optional)
    bedroom1_size = models.CharField(max_length=50, blank=True)
    bedroom2_size = models.CharField(max_length=50, blank=True)
    bedroom3_size = models.CharField(max_length=50, blank=True)
    bedroom4_size = models.CharField(max_length=50, blank=True)
    bedroom5_size = models.CharField(max_length=50, blank=True)

    # Bathrooms (1–5) sizes (all optional)
    bathroom1_size = models.CharField(max_length=50, blank=True)
    bathroom2_size = models.CharField(max_length=50, blank=True)
    bathroom3_size = models.CharField(max_length=50, blank=True)
    bathroom4_size = models.CharField(max_length=50, blank=True)
    bathroom5_size = models.CharField(max_length=50, blank=True)

    # Other rooms (optional)
    living_size   = models.CharField(max_length=50, blank=True)
    dining_size   = models.CharField(max_length=50, blank=True)
    kitchen_size  = models.CharField(max_length=50, blank=True)
    parking_size  = models.CharField(max_length=50, blank=True)
    porch_size    = models.CharField(max_length=50, blank=True)
    utility_size  = models.CharField(max_length=50, blank=True)
    store_size    = models.CharField(max_length=50, blank=True)


    # NEW
    wash_area_size     = models.CharField(max_length=50, blank=True)
    ots_size           = models.CharField("O.T.S", max_length=50, blank=True)
    hall_size          = models.CharField(max_length=50, blank=True)
    drawing_room_size  = models.CharField(max_length=50, blank=True)
    

    additional_rooms = models.CharField(max_length=255, blank=True)
    layout_style = models.CharField(max_length=100, blank=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    status = models.CharField(max_length=20, choices=BlueprintStatus.choices, default=BlueprintStatus.PENDING)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_blueprints")
    verified_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Helpers
    def bedroom_count(self):
        vals = [self.bedroom1_size, self.bedroom2_size, self.bedroom3_size, self.bedroom4_size, self.bedroom5_size]
        return len([v for v in vals if v])

    def bathroom_count(self):
        vals = [self.bathroom1_size, self.bathroom2_size, self.bathroom3_size, self.bathroom4_size, self.bathroom5_size]
        return len([v for v in vals if v])

    def mark_approved(self, admin_user):
        self.status = BlueprintStatus.APPROVED
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.save(update_fields=["status", "verified_by", "verified_at"])

    def mark_rejected(self, admin_user):
        self.status = BlueprintStatus.REJECTED
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.save(update_fields=["status", "verified_by", "verified_at"])

    def __str__(self):
        return self.title or f"Blueprint #{self.pk} by {self.owner}"
