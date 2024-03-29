from django.db import models, connection
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import CelerySignalProcessor
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client


class TenantCelerySignalProcessor(CelerySignalProcessor):
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

    def handle_pre_delete(self, sender, instance, **kwargs):
        """Handle removing of instance object from related models instance.
        We need to do this before the real delete otherwise the relation
        doesn't exists anymore and we can't get the related models instance.
        """
        self.prepare_registry_delete_related_task(instance)

    def handle_delete(self, sender, instance, **kwargs):
        """Handle delete.

        Given an individual model instance, delete the object from index.
        """
        self.prepare_registry_delete_task(instance)

    def prepare_registry_delete_related_task(self, instance):
        """
        Select its related instance before this instance was deleted.
        And pass that to celery.
        """
        action = 'index'
        tenant = connection.tenant.schema_name
        for doc in registry._get_related_doc(instance):
            doc_instance = doc(related_instance_to_ignore=instance)
            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None
            if related is not None:
                doc_instance.update(related)
                if isinstance(related, models.Model):
                    object_list = [related]
                else:
                    object_list = related
                bulk_data = list(doc_instance._get_actions(object_list, action))

                self.registry_delete_task.delay(doc_instance, bulk_data, tenant)

    @shared_task()
    def registry_delete_task(doc_instance, data, tenant):
        """
        Handle the bulk delete data on the registry as a Celery task.
        The different implementations used are due to the difference between delete and update operations.
        The update operation can re-read the updated data from the database to ensure eventual consistency,
        but the delete needs to be processed before the database record is deleted to obtain the associated data.
        """
        with LocalTenant(Client.objects.get(schema_name=tenant)):
            doc_instance._bulk(data, parallel=True)

    def prepare_registry_delete_task(self, instance):
        """
        Get the prepare did before database record deleted.
        """
        tenant = connection.tenant.schema_name
        action = 'delete'
        for doc in registry._models[instance.__class__]:
            doc_instance = doc()
            bulk_data = list(doc_instance.get_actions([instance], action))

            self.registry_delete_task.delay(
                doc_instance, bulk_data, tenant
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
