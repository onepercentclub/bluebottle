from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model


def get_organization_model():
    """
    Returns the Organization model that is active in this BlueBottle project.

    (Based on ``django.contrib.auth.get_user_model``)
    """
    try:
        app_label, model_name = settings.ORGANIZATIONS_ORGANIZATION_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_ORGANIZATION_MODEL must be of the form 'app_label.model_name'")

    org_model = get_model(app_label, model_name)
    if org_model is None:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_ORGANIZATION_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.ORGANIZATIONS_ORGANIZATION_MODEL))

    return org_model
