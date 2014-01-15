from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model


def get_project_model():
    """
    Returns the Project model that is active in this BlueBottle project.

    (Based in ``django.contrib.auth.get_user_model``)
    """
    try:
        app_label, model_name = settings.STANDARD_PROJECT_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "STANDARD_PROJECT_MODEL must be of the form 'app_label.model_name'")

    project_model = get_model(app_label, model_name)
    if project_model is None:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.AUTH_USER_MODEL))

    return project_model
