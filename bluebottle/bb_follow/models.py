from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from django.dispatch import receiver
from bluebottle.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from bluebottle.utils.model_dispatcher import get_user_model
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
    from bluebottle.wallposts.models import WallPost, Reaction

    # A WallPost is created by user
    if created and isinstance(instance, WallPost):

        # Create a Follow to the specific Project or Task if a WallPost was created
        if isinstance(instance.content_object, BaseProject) or isinstance(instance.content_object, BaseTask):
            user = instance.author
            if user and instance.content_object:

                content_type = ContentType.objects.get_for_model(instance.content_object)

                # A Follow object should link the project / task to the user, not the wallpost and the user 
                try:
                    follow = Follow.objects.get(user=user,
                                                object_id=instance.content_object.id,
                                                content_type=instance.content_type)
                except Follow.DoesNotExist:
                    follow = Follow(user=user, followed_object=instance.content_object)
                    follow.save()        

    # A Reaction is created by user
    if isinstance(instance, Reaction):
        # Create a Follow to the specific Project or Task if a Reaction was created
        if isinstance(instance.wallpost.content_object, BaseProject) or isinstance(instance.wallpost.content_object, BaseTask):
            user = instance.author
            if user and instance.wallpost.content_object:

                content_type = ContentType.objects.get_for_model(instance.wallpost.content_object)

                # A Follow object should link the project / task to the user, not the wallpost and the user 
                try:
                    follow = Follow.objects.get(user=user,
                                                object_id=instance.wallpost.content_object.id,
                                                content_type=content_type)
                except Follow.DoesNotExist:
                    follow = Follow(user=user, followed_object=instance.wallpost.content_object)
                    follow.save()    

    # A user does a donation
    if created and isinstance(instance, BaseDonation):
        # Create a Follow to the specific Project or Task if a donation was made
        user = instance.user

        if user and instance.project:

            content_type = ContentType.objects.get_for_model(instance.project)

            # A Follow object should link the project to the user, not the donation and the user 
            try:
                follow = Follow.objects.get(user=user, 
                                            object_id=instance.project.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                follow = Follow(user=user, followed_object=instance.project)
                follow.save()    
       

@receiver(post_save)
def email_followers(sender, instance, created, **kwargs):
    from bluebottle.wallposts.models import WallPost, Reaction

    if isinstance(instance, WallPost):
        content_type = ContentType.objects.get_for_model(instance.content_object) #content_type references project
        followers = Follow.objects.filter(content_type=content_type, object_id=instance.object_id).distinct()

        wallpost_text = instance.text
        
        for follower in followers:
            email = follower.user.email
            send_mail(
                    template_name='wallpost_mail.mail',
                    subject="Mail with the wallpost",
                    to=follower.user,
                    followed_object=follower.followed_object,
                    link='NO LINK'
                )