from bluebottle.utils.model_dispatcher import get_model_class
from bluebottle.utils.utils import import_class
from django.core.exceptions import ImproperlyConfigured


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
