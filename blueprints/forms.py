from django import forms
from .models import PlotBlueprint

class PlotBlueprintForm(forms.ModelForm):
    class Meta:
        model = PlotBlueprint
        fields = [
            "title", "image",

            # Plot size (searchable)
            "plot_width", "plot_height", "plot_unit",

            # Bedrooms
            "bedroom1_size","bedroom2_size","bedroom3_size","bedroom4_size","bedroom5_size",

            # Bathrooms
            "bathroom1_size","bathroom2_size","bathroom3_size","bathroom4_size","bathroom5_size",

            # Other rooms (existing)
            "living_size","dining_size","kitchen_size","parking_size","porch_size","utility_size","store_size",

            # NEW other rooms
            "wash_area_size","ots_size","hall_size","drawing_room_size",

            # Meta
            "additional_rooms","layout_style","total_area",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional title (e.g., 25X25)"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),

            "plot_width":  forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g., 40"}),
            "plot_height": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g., 60"}),
            "plot_unit":   forms.Select(attrs={"class": "form-select"}, choices=PlotBlueprint.Units.choices),

            # Bedrooms
            "bedroom1_size": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 12x12"}),
            "bedroom2_size": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 11x12"}),
            "bedroom3_size": forms.TextInput(attrs={"class": "form-control"}),
            "bedroom4_size": forms.TextInput(attrs={"class": "form-control"}),
            "bedroom5_size": forms.TextInput(attrs={"class": "form-control"}),

            # Bathrooms
            "bathroom1_size": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 5x7"}),
            "bathroom2_size": forms.TextInput(attrs={"class": "form-control"}),
            "bathroom3_size": forms.TextInput(attrs={"class": "form-control"}),
            "bathroom4_size": forms.TextInput(attrs={"class": "form-control"}),
            "bathroom5_size": forms.TextInput(attrs={"class": "form-control"}),

            # Other rooms (existing)
            "living_size":   forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 14x14"}),
            "dining_size":   forms.TextInput(attrs={"class": "form-control"}),
            "kitchen_size":  forms.TextInput(attrs={"class": "form-control"}),
            "parking_size":  forms.TextInput(attrs={"class": "form-control"}),
            "porch_size":    forms.TextInput(attrs={"class": "form-control"}),
            "utility_size":  forms.TextInput(attrs={"class": "form-control"}),
            "store_size":    forms.TextInput(attrs={"class": "form-control"}),

            # NEW fields
            "wash_area_size":    forms.TextInput(attrs={"class": "form-control"}),
            "ots_size":          forms.TextInput(attrs={"class": "form-control"}),
            "hall_size":         forms.TextInput(attrs={"class": "form-control"}),
            "drawing_room_size": forms.TextInput(attrs={"class": "form-control"}),

            # Meta
            "additional_rooms": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., servant room, study"}),
            "layout_style":     forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Modern, Traditional"}),
            "total_area":       forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g., 1200"}),
        }
