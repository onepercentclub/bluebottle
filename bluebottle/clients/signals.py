from django.db import connection
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import CelerySignalProcessor
from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client

from django_elasticsearch_dsl.signals import RealTimeSignalProcessor


class TenantCelerySignalProcessor(RealTimeSignalProcessor):
    """Celery signal processor.

    Allows automatic updates on the index as delayed background tasks using
    Celery.

    NB: We cannot process deletes as background tasks.
    By the time the Celery worker would pick up the delete job, the
    model instance would already deleted. We can get around this by
    setting Celery to use `pickle` and sending the object to the worker,
    but using `pickle` opens the application up to security concerns.
    """

    def __init__(self, *args, **kwargs):
        self.models = registry.get_models()

        self.related_models = []

        for doc in registry.get_documents():
            for related_model in doc.Django.related_models:
                self.related_models.append(related_model)

        super().__init__(*args, **kwargs)

    def handle_save(self, sender, instance, **kwargs):
        """Handle save with a Celery task.

        Given an individual model instance, update the object in the index.
        Update the related objects either.
        """
        pk = instance.pk
        app_label = instance._meta.app_label
        model_name = instance.__class__.__name__

        tenant = connection.tenant.schema_name
        if sender in self.models:
            self.registry_update_task.apply_async(
                args=[pk, app_label, model_name, tenant], countdown=2
            )

        if sender in self.related_models:

            self.registry_update_related_task.apply_async(
                args=[pk, app_label, model_name, tenant], countdown=2
            )

    @shared_task()
    def registry_update_task(pk, app_label, model_name, tenant):
        """Handle the update on the registry as a Celery task."""
        with LocalTenant(Client.objects.get(schema_name=tenant)):
            CelerySignalProcessor.registry_update_task(pk, app_label, model_name)

    @shared_task()
    def registry_update_related_task(pk, app_label, model_name, tenant):
        """Handle the related update on the registry as a Celery task."""
        with LocalTenant(Client.objects.get(schema_name=tenant)):
            CelerySignalProcessor.registry_update_related_task(pk, app_label, model_name)
