import mails

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model


def get_task_model():
    """
    Returns the Task model that is active in this BlueBottle project.

    (Based on ``django.contrib.auth.get_user_model``)
    """
    try:
        app_label, model_name = settings.TASKS_TASK_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "TASKS_TASK_MODEL must be of the form 'app_label.model_name'")

    task_model = get_model(app_label, model_name)
    if task_model is None:
        raise ImproperlyConfigured(
            "TASKS_TASK_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.TASKS_TASK_MODEL))

    return task_model
