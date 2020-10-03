from builtins import object
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Case, When, fields
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.utils.timezone import now
from parler.managers import TranslatableQuerySet, TranslatableManager
from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet

try:
    from django.db.models.expressions import Subquery, OuterRef
except ImportError:
    from django_subquery.expressions import Subquery, OuterRef


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
            qs = qs.filter(object_id=model._get_pk_val())
        return qs

    def for_content_type(self, content_type):
        """
        QuerySet for all models for particular content_type.
        """
        return self.get_queryset().filter(content_type=content_type)


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


class TranslatablePolymorphicQuerySet(TranslatableQuerySet, PolymorphicQuerySet):
    pass


class SortableTranslatablePolymorphicQuerySet(TranslatableQuerySet, PolymorphicQuerySet):
    queryset_class = SortableTranslatableQuerySet


class TranslatablePolymorphicManager(PolymorphicManager, TranslatableManager):
    queryset_class = TranslatablePolymorphicQuerySet


class SortableTranslatablePolymorphicManager(PolymorphicManager, TranslatableManager):
    queryset_class = SortableTranslatablePolymorphicQuerySet


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
