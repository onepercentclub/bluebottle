from django.db import models, transaction
from django.db.models import Case, When, fields
from django.db.models.query_utils import Q
from django.db.models.signals import pre_save, post_save
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.timezone import now

from django_subquery.expressions import Subquery, OuterRef

from parler.managers import TranslatableQuerySet, TranslatableManager


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


class SortableTranslatableQuerySet(TranslatableQuerySet):
    def order_by(self, *field_names):
        obj = self._clone()
        obj.query.clear_ordering(force_empty=False)

        for field_name in field_names:
            if field_name.startswith('translations__'):
                (_, field) = field_name.split('__')
                sub_query = self.model.translations.field.model.objects.filter(
                    master=OuterRef('pk')
                ).annotate(
                    is_current_language=Case(
                        When(language_code=self._language, then=True),
                        default=False,
                        output_field=fields.BooleanField()
                    )
                ).order_by(
                    '-is_current_language'
                ).values(
                    field
                )[:1]

                obj = obj.annotate(
                    **{'translated_{}'.format(field): Subquery(sub_query)}
                ).order_by('translated_{}'.format(field))

        field_names = [
            field_name.replace('translations__', 'translated_') for field_name in field_names
        ]

        obj.query.add_ordering(*field_names)

        return obj


class SortableTranslatableManager(TranslatableManager):
    queryset_class = SortableTranslatableQuerySet


class PublishedQuerySet(QuerySet):

    def published(self):
        """
        Return only published entries
        """
        qs = self
        qs = qs.filter(status='published')
        qs = qs.filter(
            Q(publication_date__isnull=True) |
            Q(publication_date__lte=now())
        )
        qs = qs.filter(
            Q(publication_end_date__isnull=True) |
            Q(publication_end_date__gte=now())
        )
        return qs


class PublishedManager(models.Manager):
    def get_queryset(self):
        return PublishedQuerySet(self.model, using=self._db)

    def published(self):
        """
        Return only published entries
        """
        return self.get_queryset().published()
