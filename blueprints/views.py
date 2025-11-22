from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from accounts.models import Roles
from .forms import PlotBlueprintForm
from .models import PlotBlueprint, BlueprintStatus


import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import PlotBlueprint, BlueprintStatus



import json
import re
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import PlotBlueprint, BlueprintStatus


def is_vendor(user):
    return user.is_authenticated and (user.role == Roles.VENDOR or user.is_superuser)

@login_required
@user_passes_test(is_vendor)
def vendor_list(request):
    items = PlotBlueprint.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "blueprints/vendor_list.html", {"items": items})

@login_required
@user_passes_test(is_vendor)
def vendor_create(request):
    if not getattr(request.user, "email_verified", False):
        messages.error(request, "Please verify your email before creating a dataset.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = PlotBlueprintForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.status = BlueprintStatus.PENDING
            obj.save()
            messages.success(request, "Dataset created and submitted for review.")
            return redirect("blueprints:vendor_list")
    else:
        form = PlotBlueprintForm()

    # pass obj=None so template's preview block doesn't error
    return render(request, "blueprints/form.html", {"form": form, "title": "Create Dataset", "obj": None})

@login_required
@user_passes_test(is_vendor)
def vendor_edit(request, pk):
    obj = get_object_or_404(PlotBlueprint, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PlotBlueprintForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Dataset updated.")
            return redirect("blueprints:vendor_list")
    else:
        form = PlotBlueprintForm(instance=obj)
    return render(request, "blueprints/form.html", {"form": form, "title": "Edit Dataset", "obj": obj})

@login_required
@user_passes_test(is_vendor)
def vendor_delete(request, pk):
    obj = get_object_or_404(PlotBlueprint, pk=pk, owner=request.user)
    if request.method == "POST":
        obj.delete()
        messages.info(request, "Dataset deleted.")
        return redirect("blueprints:vendor_list")
    return render(request, "blueprints/confirm_delete.html", {"obj": obj})


@login_required
def detail(request, pk):
    obj = get_object_or_404(PlotBlueprint, pk=pk)

    # Only owner can see non-approved; admins can see all; others only APPROVED
    if obj.owner != request.user and obj.status != BlueprintStatus.APPROVED and not request.user.is_superuser:
        messages.error(request, "This blueprint is not available.")
        return redirect("blueprints:vendor_list" if is_vendor(request.user) else "accounts:dashboard")

    bedroom_fields = ["bedroom1_size","bedroom2_size","bedroom3_size","bedroom4_size","bedroom5_size"]
    bathroom_fields = ["bathroom1_size","bathroom2_size","bathroom3_size","bathroom4_size","bathroom5_size"]

    return render(
        request,
        "blueprints/detail.html",
        {
            "obj": obj,
            "bedroom_fields": bedroom_fields,
            "bathroom_fields": bathroom_fields,
        },
    )

FEET_PER_METER = Decimal("3.280839895")  # 1 m = 3.28084 ft

def _normalize_to_feet(width, height, unit):
    """Return (width_ft, height_ft) as Decimal, rounded to 2 decimals."""
    try:
        w = Decimal(str(width))
        h = Decimal(str(height))
    except (InvalidOperation, TypeError):
        return None, None
    if unit == "m":
        w = (w * FEET_PER_METER)
        h = (h * FEET_PER_METER)
    # round for comparison tolerance
    return w.quantize(Decimal("0.01")), h.quantize(Decimal("0.01"))


@require_POST
def api_search_by_size(request):
    """
    POST JSON: { "width": 25, "height": 25 }
    Build token '25X25' and search title only (case-insensitive).
    Matches: '25X25', '25x25', '25 X 25', '25×25'
    Also matches swapped order.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    width = data.get("width")
    height = data.get("height")

    # Basic validation
    try:
        # normalize to plain integers if possible (25.0 -> 25), else keep as string
        def norm(n):
            d = Decimal(str(n))
            return str(int(d)) if d == d.to_integral() else str(d.normalize())
        w_txt = norm(width)
        h_txt = norm(height)
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({"error": "Invalid width/height"}, status=400)

    # Build a regex that matches:
    # w[x|X|×]h  (with optional spaces), OR the swapped h[x|X|×]w
    # \b helps avoid partial matches like 125x25
    w = re.escape(w_txt)
    h = re.escape(h_txt)
    pat_direct = rf"\b{w}\s*[xX×]\s*{h}\b"
    pat_swap   = rf"\b{h}\s*[xX×]\s*{w}\b"
    regex = rf"(?:{pat_direct})|(?:{pat_swap})"

    qs = PlotBlueprint.objects.filter(status=BlueprintStatus.APPROVED)
    hit = qs.filter(title__iregex=regex).first()

    if hit:
        return JsonResponse({"found": True, "id": hit.id})
    return JsonResponse({"found": False})