import factory

from django.core.files.uploadedfile import SimpleUploadedFile

from bluebottle.wallposts.models import TextWallpost, Reaction, SystemWallpost, MediaWallpost, MediaWallpostPhoto

from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory


class TextWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TextWallpost

    content_object = factory.SubFactory(ProjectFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: 'Text Wall Post {0}'.format(n))


    # author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('author'), related_name="%(class)s_wallpost", blank=True, null=True)
    # editor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('editor'), blank=True, null=True, help_text=_("The last user to edit this wallpost."))
    #
    # # The metadata for the wall post.
    # created = CreationDateTimeField(_('created'))
    # updated = ModificationDateTimeField(_('updated'))
    # deleted = models.DateTimeField(_('deleted'), blank=True, null=True)
    # ip_address = models.IPAddressField(_('IP address'), blank=True, null=True, default=None)
    #
    # # Generic foreign key so we can connect it to any object.
    # content_type = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    # object_id = models.PositiveIntegerField(_('object ID'))
    # content_object = generic.GenericForeignKey('content_type', 'object_id')


class SystemWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SystemWallpost


class ReactionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Reaction


class MediaWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = MediaWallpost

    content_object = factory.SubFactory(ProjectFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: 'Media Wall Post {0}'.format(n))


class MediaWallpostPhotoFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = MediaWallpostPhoto

    mediawallpost = factory.SubFactory(MediaWallpostFactory)
    photo = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
