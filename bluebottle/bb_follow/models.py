from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from bluebottle.utils.model_dispatcher import get_user_model

USER_MODEL = get_user_model()


class Follow(models.Model):
    """
    Generic Follow class. A Follow object is a generic reference between a user and another Django model.
    """

    user = models.ForeignKey(USER_MODEL)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    followed_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        if self.content_object:
            return str(self.content_object)
        return self.id

