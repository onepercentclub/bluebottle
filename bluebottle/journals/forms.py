from django.forms.models import modelform_factory


def journalform_factory(model):
    return modelform_factory(model, exclude=('user_reference',))
