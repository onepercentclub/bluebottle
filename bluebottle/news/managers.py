"""
The manager class for the blog models
"""
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.utils.timezone import now


class NewsItemQuerySet(QuerySet):
    def published(self):
        """
        Return only published entries
        """
        from .models import NewsItem

        qs = self
        qs = qs.filter(status=NewsItem.PostStatus.published)
        qs = qs.filter(
            Q(publication_date__isnull=True) | Q(publication_date__lte=now()))
        qs = qs.filter(Q(publication_end_date__isnull=True) | Q(
            publication_end_date__gte=now()))
        return qs


class NewsItemManager(models.Manager):
    """
    Extra methods attached to ``BlogPost.objects`` .
    """

    def get_queryset(self):
        return NewsItemQuerySet(self.model, using=self._db)

    def published(self):
        """
        Return only published entries
        """
        return self.get_queryset().published()
