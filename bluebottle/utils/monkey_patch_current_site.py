import django.contrib.sites.shortcuts
from django.contrib.sites.requests import RequestSite


def get_current_site(request):
    """
    Check if contrib.sites is installed and return either the current
    ``Site`` object or a ``RequestSite`` object based on the request.
    """
    return RequestSite(request)


django.contrib.sites.shortcuts.get_current_site = get_current_site
