from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from django.dispatch import receiver
from bluebottle.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from bluebottle.utils.model_dispatcher import get_user_model, get_fundraiser_model, get_donation_model
from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_tasks.models import BaseTask, BaseTaskMember
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

    def validate_unique(self, exclude=None):
        qs = Follow.objects.filter(user=self.user, content_type=self.content_type, object_id=self.object_id)
        if qs.count() > 0:
            return False
        return True

    def save(self, *args, **kwargs):
        if self.validate_unique():
            super(Follow, self).save(*args, **kwargs)


@receiver(post_save)
def create_follow(sender, instance, created, **kwargs):
    """ 
        Create a Follow object when a user follows a Project or Task. This signal handler determines the type of object that is created
        and creates the Follow object with the correct link between objects.

        A user starts following a project/task when:
            - user creates a WallPost on a project, task or fundraise wall, (user will follow, the project or task)
            - user does a donation to a project (user will follow project)
            - user applies for a task, i.e. a task member is created (user will follow task),
            - user creates a task for a project (user will follow project),
            - user creates a fundraiser for a project (user will follow project) 

            Users do not follow their own project or task.

    """
    from bluebottle.wallposts.models import WallPost, Reaction # Imported inside the signal to prevent circular imports

    # A WallPost is created by user
    if created and isinstance(instance, WallPost):

        # Create a Follow to the specific Project or Task if a WallPost was created
        if isinstance(instance.content_object, BaseProject) or isinstance(instance.content_object, BaseTask) or isinstance(instance.content_object, BaseFundRaiser):
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

                    # Check that the fundraiser is not the project owner
                    if isinstance(instance.content_object, BaseFundRaiser) and instance.content_object.project.owner != user and instance.content_object.owner != user:
                        follow = Follow(user=user, followed_object=instance.content_object.project)
                        follow.save()              

    # For now, posting a a reaction does not make you a follower. This code is left in commented because it might be re-enabled soon.
    # # A Reaction is created by user
    # if isinstance(instance, Reaction):
    #     # Create a Follow to the specific Project or Task if a Reaction was created
    #     if isinstance(instance.wallpost.content_object, BaseProject) or isinstance(instance.wallpost.content_object, BaseTask):
    #         user = instance.author
    #         if user and instance.wallpost.content_object:

    #             content_type = ContentType.objects.get_for_model(instance.wallpost.content_object)

    #             # A Follow object should link the project / task to the user, not the wallpost and the user 
    #             try:
    #                 follow = Follow.objects.get(user=user,
    #                                             object_id=instance.wallpost.content_object.id,
    #                                             content_type=content_type)
    #             except Follow.DoesNotExist:
    #                 # Check that a project owner is not the user
    #                 if isinstance(instance.wallpost.content_object, BaseProject) and instance.wallpost.content_object.owner != user:
    #                     follow = Follow(user=user, followed_object=instance.wallpost.content_object)
    #                     follow.save()
    #                 # Check that a task author is not the user
    #                 if isinstance(instance.wallpost.content_object, BaseTask) and instance.wallpost.content_object.author != user:
    #                     follow = Follow(user=user, followed_object=instance.wallpost.content_object)
    #                     follow.save()      

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

    # A user applies for a task
    if created and isinstance(instance, BaseTaskMember):
        # Create a Follow to the specific Task if a user applies for the task
        user = instance.member

        if user and instance.task:

            content_type = ContentType.objects.get_for_model(instance.task)

            try:
                follow = Follow.objects.get(user=user, 
                                            object_id=instance.task.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != instance.task.author and user != instance.task.project.owner:
                    follow = Follow(user=user, followed_object=instance.task)
                    follow.save()        


    # A user creates a task for a project
    if created and isinstance(instance, BaseTask):
        # Create a Follow to the specific Task if a task author is not the owner of the task 
        user = instance.author

        if user and instance:

            content_type = ContentType.objects.get_for_model(instance)

            try:
                follow = Follow.objects.get(user=user, 
                                            object_id=instance.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != instance.project.owner:
                    follow = Follow(user=user, followed_object=instance.project)
                    follow.save()

    # A user creates a fundraiser for a project
    if created and isinstance(instance, BaseFundRaiser):
        # Create a Follow to the specific project and the fundraiser 
        user = instance.owner

        if user and instance:

            content_type = ContentType.objects.get_for_model(instance.project)

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
    """ 
        When a Wallpost is created, project owners, task owners and fundraiser owners can check a box wether to email their followers. This 
        signal handler looksup the appropriate followers depending on the type of page (project, task, fundraiser). It then sends out an email
        to those followers if they have campaign notifications enabled.
    """
    from bluebottle.wallposts.models import WallPost

    if isinstance(instance, WallPost):
        if instance.email_followers:

            content_type = ContentType.objects.get_for_model(instance.content_object) #content_type references project

            # Determine if this wallpost is on a Project page, Task page, or Fundraiser page. Required because of different Follow object lookup  
            mailers = set() # Contains unique user objects
            
            if isinstance(instance.content_object, BaseProject):
                # Send update to all task owners, all fundraisers, all people who donated and all people who are following (i.e. posted to the wall)
                followers = Follow.objects.filter(content_type=content_type, object_id=instance.content_object.id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]

            if isinstance(instance.content_object, BaseTask):
                # Send update to all task members and to people who posted to the wall --> Follower
                followers = Follow.objects.filter(content_type=content_type, object_id=instance.object_id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]

            if isinstance(instance.content_object, BaseFundRaiser):
                # Send update to all people who donated or posted to the wall --> Followers
                content_type = ContentType.objects.get_for_model(instance.content_object.project)
                followers = Follow.objects.filter(content_type=content_type, object_id=instance.object_id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]           

            wallpost_text = instance.text

            for mailee in mailers:
                send_mail(
                        template_name='wallpost_mail.mail',
                        subject="Mail with the wallpost",
                        wallpost_text=wallpost_text,
                        to=mailee,
                        link='NO LINK'
                    )
