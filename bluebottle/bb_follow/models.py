from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.votes.models import Vote


class Follow(models.Model):
    """
    Generic Follow class. A Follow object is a generic reference between a
    user and another Django model.
    """

    user = models.ForeignKey('members.Member')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    followed_object = fields.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        if self.followed_object:
            return unicode(self.followed_object)
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
            super(Follow, self).save(*args, **kwargs)


def _create_follow_object(followed_object, user):
    content_type = ContentType.objects.get_for_model(followed_object)
    if not Follow.objects.filter(user=user, object_id=followed_object.id, content_type=content_type).count():
        Follow.objects.create(user=user, object_id=followed_object.id, content_type=content_type)


@receiver(post_save)
def create_follow(sender, instance, created, **kwargs):
    """
        Create a Follow object when a user follows a Project or Task. This
        signal handler determines the type of object that is created
        and creates the Follow object with the correct link between objects.

        A user starts following a project/task when:
            - user creates a Wallpost on a project, task or fundraise wall,
            (user will follow, the project or task)
            - user does a donation to a project (user will follow project)
            - user applies for a task, i.e. a task member is created (user will
             follow task),
            - user creates a task for a project (user will follow project),
            - user creates a fundraiser for a project (user will follow
              project)
            - user votes on a project

            Users do not follow their own project or task.

    """
    if isinstance(instance, Vote):
        user = instance.voter
        followed_object = instance.project

        if not user or not followed_object:
            return

        if user != followed_object.owner:
            _create_follow_object(followed_object, user)
