from django.db import models, transaction
from django.db.models.signals import pre_save, post_save
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode


class GenericForeignKeyManagerMixin(object):
    """
    Manager for models that use generic foreign keys based on CommentManager from django.crontrib.comments.
    """

    def for_model(self, model):
        """
        QuerySet for all objects for a particular model (either an instance or a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_queryset().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_id=force_unicode(model._get_pk_val()))
        return qs

    def for_content_type(self, content_type):
        """
        QuerySet for all models for particular content_type.
        """
        return self.get_queryset().filter(content_type=content_type)



class UpdateSignalsQuerySet(QuerySet):
    """ Queryset that sends signals when calling update instead of updating models one by one.
    """
    @transaction.atomic
    def update(self, **kwargs):
        for instance in self:
            pre_save.send(sender=instance.__class__, instance=instance, raw=False,
                          using=self.db, update_fields=kwargs.keys())

        result = super(UpdateSignalsQuerySet, self.all()).update(**kwargs)
        for instance in self:
            for key, value in kwargs.items():
                # Fake setting off values from kwargs
                setattr(instance, key, value)

            post_save.send(sender=instance.__class__, instance=instance, created=False,
                           raw=False, using=self.db, update_fields=kwargs.keys())
        return result

    update.alters_data = True
