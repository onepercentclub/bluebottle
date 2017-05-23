from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = 'bluebottle.analytics'

    def ready(self):
        import bluebottle.analytics.signals  # noqa
