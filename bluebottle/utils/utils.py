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

def get_project_model():
    """
    Returns the Project model that is active in this BlueBottle project.

    (Based on ``django.contrib.auth.get_user_model``)
    """

    try:
        app_label, model_name = settings.PROJECTS_PROJECT_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "PROJECTS_PROJECT_MODEL must be of the form 'app_label.model_name'")

    project_model = get_model(app_label, model_name)
    if project_model is None:
        raise ImproperlyConfigured(
            "PROJECTS_PROJECT_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.PROJECTS_PROJECT_MODEL))

    return project_model


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


def get_organizationmember_model():
    """
    Returns the OrganizationMember models
    """
    try:
        app_label, model_name = settings.ORGANIZATIONS_MEMBER_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_MEMBER_MODEL must be of the form 'app_label.model_name'")

    org_member_model = get_model(app_label, model_name)
    if org_member_model is None:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_MEMBER_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.ORGANIZATIONS_MEMBER_MODEL))

    return org_member_model


def get_organizationdocument_model():
    """
    Returns the Organization model that is active in this BlueBottle project.

    (Based on ``django.contrib.auth.get_user_model``)
    """
    try:
        app_label, model_name = settings.ORGANIZATIONS_DOCUMENT_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_DOCUMENT_MODEL must be of the form 'app_label.model_name'")

    org_document_model = get_model(app_label, model_name)
    if org_document_model is None:
        raise ImproperlyConfigured(
            "ORGANIZATIONS_DOCUMENT_MODEL refers to model '{0}' that has not been "
            "installed".format(settings.ORGANIZATIONS_DOCUMENT_MODEL))

    return org_document_model


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


def get_model_class(model_name=None, a=None):
    """
    Returns a model class
    model_name: The model eg 'User' or 'Project'
    """

    if model_name == 'AUTH_USER_MODEL':
        model = get_user_model()
    else:
        model_path = getattr(settings, model_name)
        try:
            app_label, model_class_name = model_path.split('.')
        except ValueError:
            raise ImproperlyConfigured(
                "{0} must be of the form 'app_label.model_name'").format(model_name)

        model = get_model(app_label, model_class_name)
        if model is None:
            raise ImproperlyConfigured(
                "{0} refers to model '{0}' that has not been "
                "installed".format(model_name))

    return model


def import_class(cl):
    d = cl.rfind(".")
    class_name = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [class_name])
    return getattr(m, class_name)


def get_serializer_class(model_name=None, serializer_type='default'):
    """
    Returns a serializer
    model_name: The model eg 'User' or 'Project'
    serializer_type: The serializer eg 'preview' or 'manage'
    """

    model = get_model_class(model_name)

    if serializer_type == 'manage':
        try:
            serializer_name = model._meta.manage_serializer
        except AttributeError:
            serializer_name = model.Meta.manage_serializer
    elif serializer_type == 'preview':
        try:
            serializer_name = model._meta.preview_serializer
        except AttributeError:
            serializer_name = model.Meta.preview_serializer
    elif serializer_type == 'default':
        try:
            serializer_name = model._meta.default_serializer
        except AttributeError:
            serializer_name = model.Meta.default_serializer
    else:
        raise ImproperlyConfigured(
            "Unknown serializer type '{0}'".format(serializer_type))

    serializer_model = import_class(serializer_name)

    if serializer_model is None:
        raise ImproperlyConfigured(
            "serializer_name refers to model '{0}' that has not been "
            "installed".format(model_name))

    return serializer_model



