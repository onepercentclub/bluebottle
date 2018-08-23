from django.core.urlresolvers import resolve


def resource_access_handler(request, resource):
    """Callback for resource access. Determines who can see the documentation for which API."""
    # See: https://django-rest-swagger.readthedocs.io/en/stable-0.3.x/settings.html#resource-access-handler

    # superusers and staff can see whatever they want
    if request.user.is_superuser or request.user.is_staff:
        return True

    # get view to assess
    if isinstance(resource, basestring):
        try:
            resolver_match = resolve('/{}/'.format(resource))
            view = resolver_match.func
        except Exception:
            return False
    else:
        view = resource.callback

    # no visibility if no permission
    for perm in view.cls.permission_classes:
        if not perm().has_permission(request, view):
            return False

    # if documentable then allow, else deny
    if getattr(view.cls, 'documentable', None):
        return True
    else:
        return False
