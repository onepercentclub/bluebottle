from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from django.dispatch import receiver
from bluebottle.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from bluebottle.utils.model_dispatcher import get_user_model, get_fundraiser_model, get_donation_model
from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_tasks.models import BaseTask
from bluebottle.bb_donations.models import BaseDonation
from bluebottle.bb_fundraisers.models import BaseFundRaiser

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
        he /she creates a WallPost or Reaction, or does a donation. Users cannot follow their own project or task.
    """
    from bluebottle.wallposts.models import WallPost, Reaction # Imported inside the signal to prevent circular imports

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
                    # Check that the project owner is not the user
                    if isinstance(instance.content_object, BaseProject) and instance.content_object.owner != user:
                        follow = Follow(user=user, followed_object=instance.content_object)
                        follow.save()
                    # Check that the task owner is not the user
                    if isinstance(instance.content_object, BaseTask) and instance.content_object.author != user:
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
                    # Check that a project owner is not the user
                    if isinstance(instance.wallpost.content_object, BaseProject) and instance.wallpost.content_object.owner != user:
                        follow = Follow(user=user, followed_object=instance.wallpost.content_object)
                        follow.save()
                    # Check that a task author is not the user
                    if isinstance(instance.wallpost.content_object, BaseTask) and instance.wallpost.content_object.author != user:
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
                if user != instance.project.owner:
                    follow = Follow(user=user, followed_object=instance.project)
                    follow.save()    


@receiver(post_save)
def email_followers(sender, instance, created, **kwargs):
    from bluebottle.wallposts.models import WallPost, Reaction

    if isinstance(instance, WallPost):
        if instance.email_followers:

            content_type = ContentType.objects.get_for_model(instance.content_object) #content_type references project

            # Determine if this wallpost is on a Project page, Task page, or Fundraiser page.
            mailers = set() # Contains user objects
            
            if isinstance(instance.content_object, BaseProject):
                # Send update to all task owners, all fundraisers, all people who donated and all people who are following (i.e. posted to the wall)
                tasks = instance.content_object.task_set.all()
                [mailers.add(task.author) for task in tasks]

                fundraisers = get_fundraiser_model().objects.filter(project=instance.content_object)
                [mailers.add(fundraiser.owner) for fundraiser in fundraisers]

                followers = Follow.objects.filter(content_type=content_type, object_id=instance.object_id).distinct()
                [mailers.add(follower.user) for follower in followers]

            if isinstance(instance.content_object, BaseTask):
                # Send update to all task members
                task_members = instance.content_object.members.all()
                [mailers.add(task_member.member) for task_member in task_members]

            if isinstance(instance.content_object, BaseFundRaiser):
                # Send update to all people who donated
                donators = get_donation_model().objects.filter(project=instance.content_object.project)
                [mailers.add(donator.order.user) for donator in donators]             

            wallpost_text = instance.text

            for mailee in mailers:
                send_mail(
                        template_name='wallpost_mail.mail',
                        subject="Mail with the wallpost",
                        wallpost_text=wallpost_text,
                        to=mailee,
                        link='NO LINK'
                    )
