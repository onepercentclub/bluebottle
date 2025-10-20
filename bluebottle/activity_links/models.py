from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from polymorphic.models import PolymorphicModel

from bluebottle.activities.models import Activity
from bluebottle.utils.fields import MoneyField


class LinkedActivity(PolymorphicModel):

    title = models.CharField(max_length=255)
    link = models.URLField()
    status = models.CharField(max_length=40)
    description = QuillField(_("Description"), blank=True)

    def __str__(self):
        return self.title


class LinkedDeed(LinkedActivity):
    """
    LinkedDeed inherits from Activity to appear in the main activity search index.
    It represents a deed activity that links to an external platform.
    """

    # Override required properties
    @property
    def succeeded_contributor_count(self):
        return 0
    
    @property
    def activity_date(self):
        return None
    
    class JSONAPIMeta(object):
        resource_name = 'activities/deeds'


class LinkedFunding(LinkedActivity):
    target = MoneyField()
    donated = MoneyField()


class LinkedDateActivity(LinkedActivity):
    start = models.DateTimeField()
    end = models.DateTimeField()


@receiver(post_save, sender=LinkedDeed)
def es_upsert_linked_deed(sender, instance, **kwargs):
    from bluebottle.activity_links.documents import LinkedDeedDocument
    LinkedDeedDocument().update(instance, refresh="wait_for")


@receiver(post_delete, sender=LinkedDeed)
def es_delete_linked_deed(sender, instance, **kwargs):
    from bluebottle.activity_links.documents import LinkedDeedDocument
    LinkedDeedDocument().delete(instance, refresh="wait_for")
