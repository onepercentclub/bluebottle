from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from polymorphic.models import PolymorphicModel

from .managers import ReactionManager, WallpostManager

WALLPOST_TEXT_MAX_LENGTH = getattr(settings, 'WALLPOST_TEXT_MAX_LENGTH', 300)
WALLPOST_REACTION_MAX_LENGTH = getattr(settings, 'WALLPOST_REACTION_MAX_LENGTH',
                                       300)

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_reaction', 'change_reaction', 'delete_reaction',
            'add_wallpost', 'change_wallpost', 'delete_wallpost',
            'add_mediawallpost', 'change_mediawallpost', 'delete_mediawallpost',
            'add_textwallpost', 'change_textwallpost', 'delete_textwallpost',
            'add_systemwallpost', 'change_systemwallpost',
            'delete_systemwallpost',
            'add_mediawallpostphoto', 'change_mediawallpostphoto',
            'delete_mediawallpostphoto',
        )
    }
}


class Wallpost(PolymorphicModel):
    """
    The Wallpost base class. This class will never be used directly because the
    content of a Wallpost is always defined
    in the child classes.

    Implementation Note: Normally this would be an abstract class but it's not
    possible to make this an abstract class
    and have the polymorphic behaviour of sorting on the common fields.
    """

    @property
    def wallpost_type(self):
        return 'unknown'

    # The user who wrote the wall post. This can be empty to support wallposts
    # without users (e.g. anonymous
    # TextWallposts, system Wallposts for donations etc.)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('author'),
                               related_name="%(class)s_wallpost", blank=True,
                               null=True)
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('editor'), blank=True,
        null=True, help_text=_("The last user to edit this wallpost."))

    # The metadata for the wall post.
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True,
                                       default=None)

    # Generic foreign key so we can connect it to any object.
    content_type = models.ForeignKey(
        ContentType, verbose_name=_('content type'),
        related_name="content_type_set_for_%(class)s")
    object_id = models.PositiveIntegerField(_('object ID'))
    content_object = fields.GenericForeignKey('content_type', 'object_id')

    share_with_facebook = models.BooleanField(default=False)
    share_with_twitter = models.BooleanField(default=False)
    share_with_linkedin = models.BooleanField(default=False)
    email_followers = models.BooleanField(default=True)

    donation = models.ForeignKey('donations.Donation',
                                 verbose_name=_("Donation"),
                                 related_name='donation',
                                 null=True, blank=True)

    # Manager
    objects = WallpostManager()
    objects_with_deleted = models.Manager()

    class Analytics:
        type = 'wallpost'
        tags = {}
        fields = {
            'id': 'id',
            'user_id': 'author.id'
        }

        def skip(self, obj, created):
            return True if obj.wallpost_type == 'system' else False

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return str(self.id)


class MediaWallpost(Wallpost):
    # The content of the wall post.

    @property
    def wallpost_type(self):
        return 'media'

    title = models.CharField(max_length=60)
    text = models.TextField(max_length=WALLPOST_REACTION_MAX_LENGTH, blank=True,
                            default='')
    video_url = models.URLField(max_length=100, blank=True, default='')

    def __unicode__(self):
        return Truncator(self.text).words(10)

        # FIXME: See how we can re-enable this
        # def save(self, *args, **kwargs):
        #     super(MediaWallpost, self).save(*args, **kwargs)
        #
        #     # Mark the photos as deleted when the MediaWallpost is deleted.
        #     if self.deleted:
        #         for photo in self.photos.all():
        #             if not photo.deleted:
        #                 photo.deleted = self.deleted
        #                 photo.save()


class MediaWallpostPhoto(models.Model):
    mediawallpost = models.ForeignKey(MediaWallpost, related_name='photos',
                                      null=True, blank=True)
    photo = models.ImageField(upload_to='mediawallpostphotos')
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True,
                                       default=None)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('author'),
                               related_name="%(class)s_wallpost_photo",
                               blank=True, null=True)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('editor'), blank=True, null=True,
                               help_text=_(
                                   "The last user to edit this wallpost photo."))


class TextWallpost(Wallpost):
    # The content of the wall post.
    @property
    def wallpost_type(self):
        return 'text'

    text = models.TextField(max_length=WALLPOST_REACTION_MAX_LENGTH)

    def __unicode__(self):
        return Truncator(self.text).words(10)


class SystemWallpost(Wallpost):
    # The content of the wall post.
    @property
    def wallpost_type(self):
        return 'system'

    text = models.TextField(max_length=WALLPOST_REACTION_MAX_LENGTH, blank=True)

    # Generic foreign key so we can connect any object to it.
    related_type = models.ForeignKey(ContentType,
                                     verbose_name=_('related type'))
    related_id = models.PositiveIntegerField(_('related ID'))
    related_object = fields.GenericForeignKey('related_type', 'related_id')

    def __unicode__(self):
        return Truncator(self.text).words(10)


class Reaction(models.Model):
    """
    A user reaction or comment to a Wallpost. This model is based on
    the Comments model from django.contrib.comments.
    """

    # Who posted this reaction. User will need to be logged in to
    # make a reaction.
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('author'),
                               related_name='wallpost_reactions')
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('editor'), blank=True,
        null=True, related_name='+',
        help_text=_("The last user to edit this reaction."))

    # The reaction text and the wallpost it's a reaction to.
    text = models.TextField(_('reaction text'),
                            max_length=WALLPOST_REACTION_MAX_LENGTH)
    wallpost = models.ForeignKey(Wallpost, related_name='reactions')

    # Metadata for the reaction.
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True,
                                       default=None)

    # Manager
    objects = ReactionManager()
    objects_with_deleted = models.Manager()

    class Meta:
        ordering = ('created',)
        verbose_name = _('Reaction')
        verbose_name_plural = _('Reactions')

    def __unicode__(self):
        s = self.text
        return Truncator(s).words(10)

import mails
import bluebottle.wallposts.signals
