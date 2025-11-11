from django.urls import path
from . import views

app_name = "blueprints"

urlpatterns = [
    # Vendor-facing CRUD
    path("vendor/", views.vendor_list, name="vendor_list"),
    path("vendor/new/", views.vendor_create, name="vendor_create"),
    path("vendor/<int:pk>/edit/", views.vendor_edit, name="vendor_edit"),
    path("vendor/<int:pk>/delete/", views.vendor_delete, name="vendor_delete"),
    # Detail page (owner or approved)
    path("<int:pk>/", views.detail, name="detail"),

    # NEW: API search
    path("api/search-by-size/", views.api_search_by_size, name="api_search_by_size"),
]
