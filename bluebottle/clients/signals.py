from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, models
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import RealTimeSignalProcessor

from bluebottle.clients.utils import LocalTenant
from bluebottle.celery import app


def _instance_exists(instance):
    return instance.__class__._default_manager.filter(pk=instance.pk).exists()


def _resolve_real_instance(instance):
    """Return the concrete polymorphic instance when available."""
    if hasattr(instance, 'get_real_instance'):
        try:
            return instance.get_real_instance()
        except Exception:
            return instance
    return instance


def _materialize_related(related):
    """
    Materialize related parents before deferring work until after commit.

    Lazy querysets that join through the deleted related child evaluate empty
    after commit, which would skip the parent reindex for child-only deletes.
    """
    if related is None:
        return None
    if isinstance(related, models.Model):
        return related
    return list(related)


def _split_related_instances(related):
    """
    Split related ES parents into still-existing vs already-deleted instances.

    Related deletes are deferred until after commit. When a parent is cascade-
    deleted in the same transaction, the deferred task still receives the stale
    in-memory parent and must not re-index it.
    """
    if related is None:
        return [], []

    if isinstance(related, models.Model):
        instances = [related]
    else:
        instances = list(related)

    existing = []
    missing = []
    for instance in instances:
        if _instance_exists(instance):
            existing.append(instance)
        else:
            missing.append(instance)
    return existing, missing


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

    def _sender_matches_registered_model(self, sender, models):
        """
        Return True when sender is a registered model or one of its parents.
        This is important for polymorphic parent models (e.g. Activity) that
        can emit signals for child instances with dedicated documents.
        """
        return any(
            sender is model or issubclass(model, sender)
            for model in models
        )

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

            related = _materialize_related(related)
            if related is None or related == []:
                continue

            registry_delete_related_task.delay_on_commit(
                doc_instance, related, tenant
            )

    def handle_delete(self, sender, instance, **kwargs):
        """Handle delete.

        Given an individual model instance, create a task to delete the object from index.
        """
        if self._sender_matches_registered_model(sender, self.models):
            registry.delete(
                _resolve_real_instance(instance),
                raise_on_error=False,
            )

    def handle_save(self, sender, instance, **kwargs):
        """Handle save with a Celery task.

        Given an individual model instance, update the object in the index.
        Update the related objects either.
        """
        instance = _resolve_real_instance(instance)
        model_info = {
            'app_label': instance._meta.app_label,
            'model_name': instance._meta.model_name,
            'pk': instance.pk
        }
        tenant = connection.tenant

        if self._sender_matches_registered_model(sender, self.models):
            registry_update_task.delay_on_commit(
                model_info, tenant
            )

        if self._sender_matches_registered_model(sender, self.related_models):
            registry_update_related_task.delay_on_commit(
                model_info, tenant
            )


@app.task
def registry_delete_related_task(doc_instance, related, tenant):
    """
    Update related instances index as a celery task.

    Related child deletes are handled after commit. If the related parent was
    also deleted in the same transaction (cascade), re-indexing would put a
    stale document back into ES. Those parents are removed from the index
    instead, with raise_on_error=False because sync handle_delete may already
    have removed them.
    """
    with LocalTenant(tenant):
        existing, missing = _split_related_instances(related)

        if existing:
            doc_instance.update(existing[0] if len(existing) == 1 else existing)

        if missing:
            doc_instance.update(
                missing[0] if len(missing) == 1 else missing,
                action='delete',
                raise_on_error=False,
            )


@app.task
def registry_update_task(model_info, tenant):
    """Handle the update on the registry as a Celery task."""
    with LocalTenant(tenant):
        # Fetch the instance fresh from the database to avoid pickling issues
        model = apps.get_model(model_info['app_label'], model_info['model_name'])
        try:
            instance = model.objects.get(pk=model_info['pk'])
            registry.update(instance)
        except model.DoesNotExist:
            # Instance was deleted between signal and task execution
            pass


@app.task
def registry_update_related_task(model_info, tenant):
    """Handle the related update on the registry as a Celery task."""
    with LocalTenant(tenant):
        # Fetch the instance fresh from the database to avoid pickling issues
        model = apps.get_model(model_info['app_label'], model_info['model_name'])
        try:
            instance = model.objects.get(pk=model_info['pk'])
            registry.update_related(instance)
        except model.DoesNotExist:
            # Instance was deleted between signal and task execution
            pass
