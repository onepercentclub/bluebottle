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

WALLPOST_TEXT_MAX_LENGTH = getattr(settings, 'WALLPOST_TEXT_MAX_LENGTH', 1000)
WALLPOST_REACTION_MAX_LENGTH = getattr(settings, 'WALLPOST_REACTION_MAX_LENGTH',
                                       1000)


class Wallpost(PolymorphicModel):
    """
    The Wallpost base class. This class will never be used directly because the
    content of a Wallpost is always defined
    in the child classes.

    Implementation Note: Normally this would be an abstract class but it's not
    possible to make this an abstract class
    and have the polymorphic behaviour of sorting on the common fields.
    """

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

    donation = models.ForeignKey('funding.Donation',
                                 verbose_name=_("Donation"),
                                 related_name='wallpost',
                                 null=True, blank=True)

    pinned = models.BooleanField(
        default=False,
        help_text=_('Pinned posts are shown first. New posts by the initiator will unpin older posts.')
    )

    # Manager
    objects = WallpostManager()
    objects_with_deleted = models.Manager()

    @property
    def wallpost_type(self):
        return 'unknown'

    @property
    def owner(self):
        return self.author

    @property
    def parent(self):
        return self.content_object

    class Analytics:
        type = 'wallpost'
        tags = {}
        fields = {
            'id': 'id',
            'user_id': 'author.id'
        }

        @staticmethod
        def skip(obj, created):
            return True if obj.wallpost_type == 'system' else False

        @staticmethod
        def timestamp(obj, created):
            if created:
                return obj.created
            else:
                return obj.updated

    class Meta:
        ordering = ('created',)
        base_manager_name = 'objects_with_deleted'
        permissions = (
            ('api_read_wallpost', 'Can view wallposts through the API'),
            ('api_add_wallpost', 'Can add wallposts through the API'),
            ('api_change_wallpost', 'Can wallposts documents through the API'),
            ('api_delete_wallpost', 'Can wallposts documents through the API'),

            ('api_read_own_wallpost', 'Can view own wallposts through the API'),
            ('api_add_own_wallpost', 'Can add own wallposts through the API'),
            ('api_change_own_wallpost', 'Can own wallposts documents through the API'),
            ('api_delete_own_wallpost', 'Can own wallposts documents through the API'),
        )

    def __unicode__(self):
        return "{} #{}".format(self.polymorphic_ctype, self.id)


class MediaWallpost(Wallpost):
    # The content of the wall post.

    @property
    def wallpost_type(self):
        return 'media'

    title = models.CharField(max_length=60, blank=True, default='')
    text = models.TextField(max_length=WALLPOST_REACTION_MAX_LENGTH, blank=True,
                            default='')
    video_url = models.URLField(max_length=100, blank=True, default='')

    def __unicode__(self):
        return Truncator(self.text).words(10)

    class Meta(Wallpost.Meta):
        permissions = (
            ('api_read_own_textwallpost', 'Can view own text wallposts through the API'),
            ('api_add_own_textwallpost', 'Can add own text wallposts through the API'),
            ('api_change_own_textwallpost', 'Can change text wallposts through the API'),
            ('api_delete_own_textwallpost', 'Can delete own text wallposts through the API'),

            ('api_read_textwallpost', 'Can view text wallposts through the API'),
            ('api_add_textwallpost', 'Can add text wallposts through the API'),
            ('api_change_textwallpost', 'Can change text wallposts through the API'),
            ('api_delete_textwallpost', 'Can delete text wallposts through the API'),

            ('api_read_mediawallpost', 'Can view media wallposts through the API'),
            ('api_add_mediawallpost', 'Can add media wallposts through the API'),
            ('api_change_mediawallpost', 'Can change media wallposts through the API'),
            ('api_delete_mediawallpost', 'Can delete media wallposts through the API'),

            ('api_read_own_mediawallpost', 'Can view own media wallposts through the API'),
            ('api_add_own_mediawallpost', 'Can add own media wallposts through the API'),
            ('api_change_own_mediawallpost', 'Can change own media wallposts through the API'),
            ('api_delete_own_mediawallpost', 'Can delete own media wallposts through the API'),

            ('api_read_mediawallpostphoto', 'Can view media wallpost photos through the API'),
            ('api_add_mediawallpostphoto', 'Can add media wallpost photos through the API'),
            ('api_change_mediawallpostphoto', 'Can change media wallpost photos through the API'),
            ('api_delete_mediawallpostphoto', 'Can delete media wallpost photos through the API'),

            ('api_read_own_mediawallpostphoto', 'Can view own media wallpost photos through the API'),
            ('api_add_own_mediawallpostphoto', 'Can add own media wallpost photos through the API'),
            ('api_change_own_mediawallpostphoto', 'Can change own media wallpost photos through the API'),
            ('api_delete_own_mediawallpostphoto', 'Can delete own media wallpost photos through the API'),
        )


class MediaWallpostPhoto(models.Model):
    mediawallpost = models.ForeignKey(MediaWallpost, related_name='photos',
                                      null=True, blank=True)
    results_page = models.BooleanField(default=True)
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

    @property
    def owner(self):
        return self.author

    @property
    def parent(self):
        return self.mediawallpost.content_object


class TextWallpost(Wallpost):
    # The content of the wall post.
    @property
    def wallpost_type(self):
        return 'text'

    @property
    def owner(self):
        return self.author

    @property
    def parent(self):
        return self.content_object

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
        return Truncator(self.text).words(10) or super(SystemWallpost, self).__unicode__()


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

    @property
    def owner(self):
        return self.author

    class Analytics:
        type = 'wallpost'
        tags = {}

        fields = {
            'id': 'id',
            'user_id': 'author.id'
        }

        @staticmethod
        def extra_tags(instance, created):
            return {'sub_type': 'reaction'}

        @staticmethod
        def timestamp(obj, created):
            if created:
                return obj.created
            else:
                return obj.updated

    class Meta:
        ordering = ('created',)
        base_manager_name = 'objects_with_deleted'
        verbose_name = _('Reaction')
        verbose_name_plural = _('Reactions')
        permissions = (
            ('api_read_reaction', 'Can view reactions through the API'),
            ('api_add_reaction', 'Can add reactions through the API'),
            ('api_change_reaction', 'Can reactions documents through the API'),
            ('api_delete_reaction', 'Can reactions documents through the API'),

            ('api_read_own_reaction', 'Can view own reactions through the API'),
            ('api_add_own_reaction', 'Can add own reactions through the API'),
            ('api_change_own_reaction', 'Can change own reactions documents through the API'),
            ('api_delete_own_reaction', 'Can delete own reactions documents through the API'),
        )

    def __unicode__(self):
        s = self.text
        return Truncator(s).words(10)


import bluebottle.wallposts.signals  # noqa
