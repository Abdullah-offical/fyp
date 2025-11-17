from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),  # '/'
    path("contact/", views.contact, name="contact"),
    path("generate-blueprint/", views.generate_blueprint, name="generate_blueprint"),
    path("property-details/", views.property_details, name="property_details"),
    path("view-blueprint/", views.view_blueprint, name="view_blueprint"),
]