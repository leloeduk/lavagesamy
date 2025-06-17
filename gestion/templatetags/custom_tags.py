from django import template

register = template.Library()

@register.filter
def status_class(status):
    if status.lower() == "payé":
        return "bg-green-500"
    elif status.lower() == "en cours":
        return "bg-yellow-500"
    else:
        return "bg-red-500"
