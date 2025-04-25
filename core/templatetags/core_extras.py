# core/templatetags/core_extras.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Allows accessing dictionary items with a variable key in templates.
    Usage: {{ my_dictionary|get_item:my_variable_key }}
    Returns None if the key doesn't exist.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None # Return None or '' if it's not a dictionary or key not found