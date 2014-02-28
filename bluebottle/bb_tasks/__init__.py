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


def get_taskmember_model():
    """
    Returns the TaskMember model
    """
    try:
        app_label, model_name = settings.TASKS_TASKMEMBER_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "TASKS_TASKMEMBER_MODEL must be of the form 'app_label.model_name'")

    taskmember_model = get_model(app_label, model_name)
    if taskmember_model is None:
        raise ImproperlyConfigured(
            "TASKS_TASKMEMBER_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.TASKS_TASKMEMBER_MODEL))

    return taskmember_model

def get_taskfile_model():
    """
    Returns the TaskFile model
    """
    try:
        app_label, model_name = settings.TASKS_TASKFILE_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "TASKS_TASKFILE_MODEL must be of the form 'app_label.model_name'")

    taskfile_model = get_model(app_label, model_name)
    if taskfile_model is None:
        raise ImproperlyConfigured(
            "TASKS_TASKFILE_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.TASKS_TASKFILE_MODEL))

    return taskfile_model

def get_skill_model():
    """
    Returns the Skill model
    """
    try:
        app_label, model_name = settings.TASKS_SKILL_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "TASKS_SKILL_MODEL must be of the form 'app_label.model_name'")

    skill_model = get_model(app_label, model_name)
    if skill_model is None:
        raise ImproperlyConfigured(
            "TASKS_SKILL_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.TASKS_SKILL_MODEL))

    return skill_model