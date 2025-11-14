# core/templatetags/form_extras.py
from django import template
register = template.Library()

@register.filter
def attr(obj, name):
    """Return obj.<name> or '' if missing."""
    return getattr(obj, name, "")
