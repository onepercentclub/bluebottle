from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.utils import translation
from bluebottle.utils.model_dispatcher import get_user_model
from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_tasks.models import BaseTask, BaseTaskMember
from bluebottle.bb_donations.models import BaseDonation
from bluebottle.bb_fundraisers.models import BaseFundraiser
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail
from bluebottle.clients import properties


USER_MODEL = get_user_model()


class Follow(models.Model):

    """
    Generic Follow class. A Follow object is a generic reference between a
    user and another Django model.
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
        qs = Follow.objects.filter(
            user=self.user, content_type=self.content_type,
            object_id=self.object_id)
        if qs.count() > 0:
            return False
        return True

    def save(self, *args, **kwargs):
        if self.validate_unique():
            super(Follow, self).save(*args, **kwargs)


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

            Users do not follow their own project or task.

    """
    if not created:
        return

    from bluebottle.wallposts.models import Wallpost, Reaction, SystemWallpost
    # Imported inside the signal to prevent circular imports

    # A Wallpost is created by user
    if isinstance(instance, Wallpost):

        # Create a Follow to the specific Project or Task if a Wallpost was
        # created
        if isinstance(instance.content_object, BaseProject) or isinstance(instance.content_object, BaseTask) or isinstance(instance.content_object, BaseFundraiser):
            user = instance.author
            if user and instance.content_object:

                content_type = ContentType.objects.get_for_model(
                    instance.content_object)

                # A Follow object should link the project / task to the user,
                # not the wallpost and the user
                try:
                    follow = Follow.objects.get(user=user,
                                                object_id=instance.content_object.id,
                                                content_type=content_type)
                except Follow.DoesNotExist:
                    # Check that the project owner is not the user
                    if isinstance(instance.content_object, BaseProject) and instance.content_object.owner != user:
                        follow = Follow(
                            user=user, followed_object=instance.content_object)
                        follow.save()
                    # Check that the task owner is not the user
                    elif isinstance(instance.content_object, BaseTask) and instance.content_object.author != user:
                        follow = Follow(
                            user=user, followed_object=instance.content_object)
                        follow.save()

                    # Check that the fundraiser is not the project owner
                    elif isinstance(instance.content_object, BaseFundraiser) and instance.content_object.project.owner != user and instance.content_object.owner != user:
                        follow = Follow(
                            user=user, followed_object=instance.content_object)
                        follow.save()

    # For now, posting a a reaction does not make you a follower. This code is left in commented because it might be re-enabled soon.
    # A Reaction is created by user
    # if isinstance(instance, Reaction):
    # Create a Follow to the specific Project or Task if a Reaction was created
    #     if isinstance(instance.wallpost.content_object, BaseProject) or isinstance(instance.wallpost.content_object, BaseTask):
    #         user = instance.author
    #         if user and instance.wallpost.content_object:

    #             content_type = ContentType.objects.get_for_model(instance.wallpost.content_object)

    # A Follow object should link the project / task to the user, not the wallpost and the user
    #             try:
    #                 follow = Follow.objects.get(user=user,
    #                                             object_id=instance.wallpost.content_object.id,
    #                                             content_type=content_type)
    #             except Follow.DoesNotExist:
    # Check that a project owner is not the user
    #                 if isinstance(instance.wallpost.content_object, BaseProject) and instance.wallpost.content_object.owner != user:
    #                     follow = Follow(user=user, followed_object=instance.wallpost.content_object)
    #                     follow.save()
    # Check that a task author is not the user
    #                 if isinstance(instance.wallpost.content_object, BaseTask) and instance.wallpost.content_object.author != user:
    #                     follow = Follow(user=user, followed_object=instance.wallpost.content_object)
    #                     follow.save()

    # A user does a donation
    elif isinstance(instance, BaseDonation):
        # Create a Follow to the specific Project or Task if a donation was
        # made

        # Don't setup following for monthly donation.
        if instance.order.order_type == 'recurring':
            return

        user = instance.user
        followed_object = instance.fundraiser or instance.project

        if user and followed_object:

            content_type = ContentType.objects.get_for_model(followed_object)

            # A Follow object should link the project to the user, not the
            # donation and the user
            try:
                follow = Follow.objects.get(user=user,
                                            object_id=followed_object.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != followed_object.owner:
                    follow = Follow(user=user, followed_object=followed_object)
                    follow.save()

    # A user applies for a task
    elif isinstance(instance, BaseTaskMember):
        # Create a Follow to the specific Task if a user applies for the task
        user = instance.member
        followed_object = instance.task

        if user and followed_object:

            content_type = ContentType.objects.get_for_model(followed_object)

            try:
                follow = Follow.objects.get(user=user,
                                            object_id=followed_object.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != followed_object.author and user != followed_object.project.owner:
                    follow = Follow(user=user, followed_object=followed_object)
                    follow.save()

    # A user creates a task for a project
    elif isinstance(instance, BaseTask):
        # Create a Follow to the specific Task if a task author is not the
        # owner of the task
        user = instance.author
        followed_object = instance.project

        if user and followed_object:

            content_type = ContentType.objects.get_for_model(followed_object)

            try:
                follow = Follow.objects.get(user=user,
                                            object_id=followed_object.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != followed_object.owner:
                    follow = Follow(user=user, followed_object=followed_object)
                    follow.save()

    # A user creates a fundraiser for a project
    elif isinstance(instance, BaseFundraiser):
        # Create a Follow to the specific project
        user = instance.owner
        followed_object = instance.project

        if user and followed_object:

            content_type = ContentType.objects.get_for_model(followed_object)

            try:
                follow = Follow.objects.get(user=user,
                                            object_id=followed_object.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != followed_object.owner:
                    follow = Follow(user=user, followed_object=followed_object)
                    follow.save()


@receiver(post_save)
def email_followers(sender, instance, created, **kwargs):
    """ 
        When a Wallpost is created, project owners, task owners and fundraiser owners can check a box wether to email their followers. This 
        signal handler looksup the appropriate followers depending on the type of page (project, task, fundraiser). It then sends out an email
        to those followers if they have campaign notifications enabled.
    """
    from bluebottle.wallposts.models import Wallpost, SystemWallpost

    if isinstance(instance, Wallpost) and not isinstance(instance, SystemWallpost):
        if instance.email_followers:
            content_type = ContentType.objects.get_for_model(
                instance.content_object)  # content_type references project

            # Determine if this wallpost is on a Project page, Task page, or
            # Fundraiser page. Required because of different Follow object
            # lookup
            mailers = set()  # Contains unique user objects
            link = None

            if isinstance(instance.content_object, BaseProject):
                # Send update to all task owners, all fundraisers, all people
                # who donated and all people who are following (i.e. posted to
                # the wall)
                followers = Follow.objects.filter(
                    content_type=content_type,
                    object_id=instance.content_object.id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('project')
                link = '/go/projects/{0}'.format(instance.content_object.slug)

            if isinstance(instance.content_object, BaseTask):
                # Send update to all task members and to people who posted to
                # the wall --> Follower
                followers = Follow.objects.filter(
                    content_type=content_type, object_id=instance.content_object.id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('task')
                link = '/go/tasks/{0}'.format(instance.content_object.id)

            if isinstance(instance.content_object, BaseFundraiser):
                # Send update to all people who donated or posted to the wall
                # --> Followers
                followers = Follow.objects.filter(
                    content_type=content_type, object_id=instance.content_object.id).distinct().exclude(user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('fundraiser')
                link = '/go/fundraisers/{0}'.format(instance.content_object.id)

            wallpost_text = instance.text

            site = tenant_url()

            full_link = site + link

            for mailee in mailers:
                if mailee.campaign_notifications:

                    cur_language = translation.get_language()

                    if mailee.primary_language:
                        translation.activate(mailee.primary_language)
                    else:
                        translation.activate(properties.LANGUAGE_CODE)

                    subject = _("New wallpost on %(name)s") % {
                        'name': instance.content_object.title}

                    translation.activate(cur_language)

                    send_mail(
                        template_name='bb_follow/mails/wallpost_mail.mail',
                        subject=subject,
                        wallpost_text=wallpost_text[:250],
                        to=mailee,
                        link=full_link,
                        follow_object=follow_object,
                        first_name=mailee.first_name,
                        author=instance.author.first_name
                    )
