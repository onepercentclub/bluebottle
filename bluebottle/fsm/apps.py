from django.apps import AppConfig


class FSMConfig(AppConfig):
    name = 'bluebottle.fsm'
    verbose_name = "FSM"

    def ready(self):
        self.module.autodiscover()
