from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model

def get_client_ip(request):
    """ A utility method that returns the client IP for the given request. """

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def set_author_editor_ip(request, obj):
    """ A utility method to set the author, editor and IP address on an object based on information in a request. """

    if not hasattr(obj, 'author'):
        obj.author = request.user
    else:
        obj.editor = request.user
    obj.ip_address = get_client_ip(request)

def get_project_phaselog_model():
    """
    Returns the Project model that is active in this BlueBottle project.

    (Based on ``django.contrib.auth.get_user_model``)
    """

    try:
        app_label, model_name = settings.PROJECTS_PHASELOG_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "PROJECTS_PHASELOG_MODEL must be of the form 'app_label.model_name'")

    project_phaselog_model = get_model(app_label, model_name)
    if project_phaselog_model is None:
        raise ImproperlyConfigured(
            "PROJECTS_PHASELOG_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.PROJECTS_PHASELOG_MODEL))

    return project_phaselog_model


def clean_for_hashtag(text):
    """
    Strip non alphanumeric charachters.

    Sometimes, text bits are made up of two parts, sepated by a slash. Split
    those into two tags. Otherwise, join the parts separated by a space.
    """
    tags = []
    bits = text.split('/')
    for bit in bits:
        # keep the alphanumeric bits and capitalize the first letter
        _bits = [_bit.title() for _bit in bit.split() if _bit.isalnum()]
        tag = "".join(_bits)
        tags.append(tag)

    return " #".join(tags)