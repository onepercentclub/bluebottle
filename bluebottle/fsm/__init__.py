from django.utils.module_loading import autodiscover_modules


class TransitionsMixin:
    pass


def autodiscover():
    autodiscover_modules('states')
    autodiscover_modules('triggers')


default_app_config = 'bluebottle.fsm.apps.FSMConfig'
