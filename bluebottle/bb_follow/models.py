from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from bluebottle.utils.model_dispatcher import get_user_model
from bluebottle.wallposts.models import WallPost, Reaction
from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_tasks.models import BaseTask
from bluebottle.bb_donations.models import BaseDonation

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
        if self.followed_object:
            return str(self.followed_object)
        return self.id


@receiver(post_save)
def create_follow(sender, instance, created, **kwargs):
    """ 
        Create a Follow object when a user follows a Project or Task. A user starts following a project/task when 
        he /she creates a WallPost or Reaction, or does a donation.
    """

    # A WallPost is created by user
    if created and isinstance(instance, WallPost):

        # Create a Follow to the specific Project or Task if a WallPost was created
        if isinstance(instance.content_object, BaseProject) or isinstance(instance.content_object, BaseTask):
            user = instance.author
            if user and instance.content_object:
                follow = Follow(user=user, followed_object=instance.content_object)
                follow.save()        

    # A Reaction is created by user
    if created and isinstance(instance, Reaction):
        # Create a Follow to the specific Project or Task if a Reaction was created
        if isinstance(instance.wallpost.content_object, BaseProject) or isinstance(instance.wallpost.content_object, BaseTask):
            user = instance.author
            if user and instance.wallpost.content_object:
                follow = Follow(user=user, followed_object=instance.wallpost.content_object)
                follow.save() 

    # A user does a donation
    if created and isinstance(instance, BaseDonation):
        # Create a Follow to the specific Project or Task if a donation was made
        user = instance.user
        if user and instance.project:
            follow = Follow(user=user, followed_object=instance.project)    
            follow.save()        
