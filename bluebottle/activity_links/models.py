from django.db import models
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from polymorphic.models import PolymorphicModel

from bluebottle.utils.fields import MoneyField


class LinkedActivity(PolymorphicModel):

    title = models.CharField(max_length=255)
    link = models.URLField()
    status = models.CharField(max_length=40)
    description = QuillField(_("Description"), blank=True)

    def __str__(self):
        return self.title


class LinkedDeed(LinkedActivity):
    pass


class LinkedFunding(LinkedActivity):
    target = MoneyField()
    donated = MoneyField()


class LinkedDateActivity(LinkedActivity):
    start = models.DateTimeField()
    end = models.DateTimeField()
