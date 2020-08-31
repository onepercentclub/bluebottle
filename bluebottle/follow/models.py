from django.db import models
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType


class Follow(models.Model):
    """
    Generic Follow class. A Follow object is a generic reference between a
    user and another Django model.
    """
    user = models.ForeignKey('members.Member', related_name='follows')
    content_type = models.ForeignKey(ContentType, related_name='follow_object')
    instance_id = models.PositiveIntegerField()
    instance = fields.GenericForeignKey('content_type', 'instance_id')

    created = models.DateTimeField(auto_now_add=True)


def follow(user, instance):
    try:
        Follow.objects.get_or_create(
            user=user,
            instance_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance)
        )
    except Follow.MultipleObjectsReturned:
        # Fix accidental double follows.
        first = Follow.objects.filter(
            user=user,
            instance_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance)
        ).first()
        Follow.objects.filter(
            user=user,
            instance_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance),
        ).exclude(
            id=first.id
        ).all().delete()


def unfollow(user, instance):
    try:
        Follow.objects.get(
            user=user,
            instance_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance)
        ).delete()
    except Follow.DoesNotExist:
        pass
