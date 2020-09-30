from django.utils.module_loading import autodiscover_modules

from django.db import models


class FSMField(models.CharField):
    pass


class TransitionsMixin:
    pass


def autodiscover():
    autodiscover_modules('states')
    autodiscover_modules('triggers')


default_app_config = 'bluebottle.fsm.apps.FSMConfig'
