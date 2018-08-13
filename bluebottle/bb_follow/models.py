from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes import fields
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from tenant_extras.utils import TenantLanguage

from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_fundraisers.models import BaseFundraiser
from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.orders.models import Order
from bluebottle.utils.email_backend import send_mail
from bluebottle.tasks.models import Task, TaskMember
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
    # A user does a donation
    if isinstance(instance, Order):
        # Create a Follow to the specific Project or Task if a donation was
        # made
        if instance.status not in ['success', 'pending']:
            return

        # Don't setup following for monthly donation.
        if instance.order_type == 'recurring':
            return

        user = instance.user

        if not instance.donations.first():
            return

        followed_object = instance.donations.first().fundraiser or instance.donations.first().project

        if not user or not followed_object:
            return

        content_type = ContentType.objects.get_for_model(followed_object)

        # A Follow object should link the project to the user, not the
        # donation and the user
        if user != followed_object.owner:
            if not Follow.objects.filter(user=user, object_id=followed_object.id, content_type=content_type).count():
                Follow.objects.create(user=user, object_id=followed_object.id, content_type=content_type)

    if not created:
        return

    # A user applies for a task
    elif isinstance(instance, TaskMember):
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

            # Also follow the project
            content_type = ContentType.objects.get_for_model(followed_object.project)
            try:
                follow = Follow.objects.get(user=user,
                                            object_id=followed_object.project.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != followed_object.author and user != followed_object.project.owner:
                    follow = Follow(user=user, followed_object=followed_object.project)
                    follow.save()

    # A user creates a task for a project
    elif isinstance(instance, Task):
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

    elif isinstance(instance, Vote):
        user = instance.voter
        project = instance.project

        if user and project:
            content_type = ContentType.objects.get_for_model(project)

            try:
                follow = Follow.objects.get(user=user,
                                            object_id=project.id,
                                            content_type=content_type)
            except Follow.DoesNotExist:
                if user != project.owner:
                    follow = Follow(user=user, followed_object=project)
                    follow.save()


@receiver(post_save)
def email_followers(sender, instance, created, **kwargs):
    """
    When a Wallpost is created, project owners, task owners and fundraiser
    owners can check a box wether to email their followers. This signal
    handler looksup the appropriate followers depending on the type of page
    (project, task, fundraiser). It then sends out an email
    to those followers if they have campaign notifications enabled.
    """
    from bluebottle.wallposts.models import Wallpost, SystemWallpost

    if not created:
        return

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
                    object_id=instance.content_object.id).distinct().exclude(
                    user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('project')
                link = '/projects/{0}'.format(instance.content_object.slug)

            if isinstance(instance.content_object, Task):
                # Send update to all task members and to people who posted to
                # the wall --> Follower
                followers = Follow.objects.filter(
                    content_type=content_type,
                    object_id=instance.content_object.id).distinct().exclude(
                    user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('task')
                link = '/tasks/{0}'.format(instance.content_object.id)

            if isinstance(instance.content_object, BaseFundraiser):
                # Send update to all people who donated or posted to the wall
                # --> Followers
                followers = Follow.objects.filter(
                    content_type=content_type,
                    object_id=instance.content_object.id).distinct().exclude(
                    user=instance.author)
                [mailers.add(follower.user) for follower in followers]
                follow_object = _('fundraiser')
                link = '/fundraisers/{0}'.format(instance.content_object.id)

            wallpost_text = instance.text

            for mailee in mailers:
                if mailee.campaign_notifications:

                    cur_language = translation.get_language()

                    if mailee.primary_language:
                        translation.activate(mailee.primary_language)
                    else:
                        translation.activate(properties.LANGUAGE_CODE)

                    with TenantLanguage(mailee.primary_language):
                        subject = _("New wallpost on %(name)s") % {
                            'name': instance.content_object.title}

                    translation.activate(cur_language)

                    send_mail(
                        template_name='bb_follow/mails/wallpost_mail.mail',
                        subject=subject,
                        wallpost_text=wallpost_text[:250],
                        to=mailee,
                        link=link,
                        unsubscribe_link='/member/profile',
                        follow_object=follow_object,
                        first_name=mailee.first_name,
                        author=instance.author.first_name
                    )
