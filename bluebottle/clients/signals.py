from django.db import connection
from django.core.exceptions import ObjectDoesNotExist

from django_elasticsearch_dsl.registries import registry
from celery import shared_task

from bluebottle.clients.utils import LocalTenant

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
            if hasattr(doc, 'Django') and hasattr(doc.Django, 'related_models'):
                for related_model in doc.Django.related_models:
                    self.related_models.append(related_model)

        super().__init__(*args, **kwargs)

    def handle_pre_delete(self, sender, instance, **kwargs):
        """Handle removing of instance object from related models instance.
        We need to do this before the real delete otherwise the relation
        doesn't exists anymore and we can't get the related models instance.
        """
        tenant = connection.tenant

        for doc in registry._get_related_doc(instance):
            doc_instance = doc(related_instance_to_ignore=instance)

            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None

            self.registry_delete_related_task.apply_async(
                [doc_instance, related, tenant], countdown=2
            )

    def handle_delete(self, sender, instance, **kwargs):
        """Handle delete.

        Given an individual model instance, create a task to delete the object from index.
        """
        if sender in self.models:
            self.registry_delete_task.apply_async(
                args=[instance, connection.tenant], countdown=2
            )

    @shared_task()
    def registry_delete_task(instance, tenant):
        """
        Delete instance in index as a celery task
        """
        with LocalTenant(tenant):
            registry.delete(instance)

    @shared_task()
    def registry_delete_related_task(doc_instance, related, tenant):
        """
        Update related instances index as a celery task.
        Implementation differs, because the object will not exist any more at this point.
        """
        with LocalTenant(tenant):
            doc_instance.update(related)

    def handle_save(self, sender, instance, **kwargs):
        """Handle save with a Celery task.

        Given an individual model instance, update the object in the index.
        Update the related objects either.
        """
        if sender in self.models:
            self.registry_update_task.apply_async(
                args=[instance, connection.tenant], countdown=2
            )

        if sender in self.related_models:
            self.registry_update_related_task.apply_async(
                args=[instance, connection.tenant], countdown=2
            )

    @shared_task()
    def registry_update_task(instance, tenant):
        """Handle the update on the registry as a Celery task."""
        with LocalTenant(tenant):
            registry.update(instance)

    @shared_task()
    def registry_update_related_task(instance, tenant):
        """Handle the related update on the registry as a Celery task."""
        with LocalTenant(tenant):
            registry.update_related(instance)
