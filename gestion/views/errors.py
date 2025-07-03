# Example: gestion/views/errors.py

from django.shortcuts import render

def custom_permission_denied_view(request, exception=None):
    return render(request, "errors/403.html", status=403)

def custom_page_not_found_view(request, exception=None):
    return render(request, "errors/404.html", status=404)

def custom_error_view(request):
    return render(request, "errors/500.html", status=500)
