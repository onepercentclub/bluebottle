from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class Follow(models.Model):
    """
    Generic Follow class. A Follow object is a generic reference between a
    user and another Django model.
    """

    user = models.ForeignKey('members.Member')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    followed_object = fields.GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        if self.followed_object:
            return str(self.followed_object)
        return self.id

    def validate_unique(self, exclude=None):
        qs = Follow.objects.filter(
            user=self.user, content_type=self.content_type,
            object_id=self.object_id)
        if qs.count() > 0:
            return False
        return True

    def save(self, *args, **kwargs):
        if self.validate_unique():
            super().save(*args, **kwargs)
