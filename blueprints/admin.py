from django.contrib import admin
from .models import PlotBlueprint, BlueprintStatus

@admin.register(PlotBlueprint)
class PlotBlueprintAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "owner__username", "owner__email")
    readonly_fields = ("verified_by", "verified_at", "created_at", "updated_at")

    actions = ["approve_selected", "reject_selected"]

    def approve_selected(self, request, queryset):
        n = 0
        for obj in queryset:
            obj.mark_approved(request.user)
            n += 1
        self.message_user(request, f"Approved {n} blueprint(s).")
    approve_selected.short_description = "Approve selected"

    def reject_selected(self, request, queryset):
        n = 0
        for obj in queryset:
            obj.mark_rejected(request.user)
            n += 1
        self.message_user(request, f"Rejected {n} blueprint(s).")
    reject_selected.short_description = "Reject selected"
