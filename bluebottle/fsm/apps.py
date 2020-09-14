from django.apps import AppConfig
from django.conf import settings


class FSMConfig(AppConfig):
    name = 'bluebottle.fsm'
    verbose_name = "FSM"

    def ready(self):
        self.module.autodiscover()
