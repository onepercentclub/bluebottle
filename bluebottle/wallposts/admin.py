from future import standard_library
standard_library.install_aliases()
import urllib.parse

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, mark_safe
from django.template.loader import render_to_string

from polymorphic.admin import (PolymorphicParentModelAdmin,
                               PolymorphicChildModelAdmin)
from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.utils.utils import set_author_editor_ip
from bluebottle.wallposts.models import SystemWallpost
from bluebottle.utils.widgets import SecureAdminURLFieldWidget

from .models import (Wallpost, MediaWallpost, TextWallpost,
                     MediaWallpostPhoto, Reaction)


class BaseWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost

    def view_online(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>',
                           obj.content_object.get_absolute_url(),
                           obj.content_object)

    view_online.short_description = _('View online')


class ReactionInline(admin.TabularInline):
    model = Reaction
    readonly_fields = ('reaction_link', 'author', 'ip_address', 'text', 'created', 'deleted')
    fields = readonly_fields
    extra = 0

    def reaction_link(self, obj):
        url = reverse('admin:wallposts_reaction_change', args=(obj.id, ))
        return format_html("<a href='{}'>Reaction #{}</a>", url, obj.id)


class MediaWallpostPhotoInline(admin.TabularInline):
    model = MediaWallpostPhoto
    extra = 0
    raw_id_fields = ('author', 'editor')

    readonly_fields = ('image_tag',)

    fields = ('image_tag', 'photo')

    def image_tag(self, obj):
        data = {}
        if obj.photo:
            data['image_full_url'] = obj.photo.url
            data['image_thumb_url'] = get_thumbnail(obj.photo, "120x120",
                                                    crop="center").url

        return mark_safe(render_to_string(
            "admin/wallposts/mediawallpost_photoinline.html", data
        ))

    image_tag.short_description = 'Preview'


class MediaWallpostAdmin(BaseWallpostAdmin):
    readonly_fields = ('ip_address', 'created', 'deleted', 'view_online', 'gallery', 'donation',
                       'share_with_facebook', 'share_with_twitter',
                       'share_with_linkedin', 'email_followers')
    fields = readonly_fields + ('text', 'author', 'editor', 'pinned')
    raw_id_fields = ('author', 'editor')
    list_display = ('created', 'view_online', 'get_text', 'thumbnail', 'author', 'deleted')
    search_fields = ('text', 'author__first_name', 'author__last_name')
    exclude = ('object_id', 'content_type')

    extra_fields = ('gallery',)

    ordering = ('-created',)
    inlines = (MediaWallpostPhotoInline, ReactionInline)

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def get_text(self, obj):
        if len(obj.text) > 150:
            return format_html(
                u'<span title="{}">{} [...]</span>',
                obj.text, obj.text[:145])

    def thumbnail(self, obj):
        data = {}
        if obj.video_url:
            data['video_url'] = obj.video_url
            if 'youtube.com' in obj.video_url:
                try:
                    urlparts = urllib.parse.urlparse(obj.video_url)
                    data['youtubeid'] = urllib.parse.parse_qs(urlparts.query)['v'][
                        0]
                except (KeyError, ValueError, IndexError):
                    pass

        photos = MediaWallpostPhoto.objects.filter(mediawallpost=obj)
        data['count'] = len(photos)
        data['remains'] = max(0, data['count'] - 1)

        if len(photos):
            if photos[0].photo:
                data['firstimage'] = get_thumbnail(photos[0].photo, "120x120",
                                                   crop="center").url
                data['firstimage_url'] = photos[0].photo.url

        return mark_safe(render_to_string("admin/wallposts/preview_thumbnail.html", data))

    def gallery(self, obj):
        data = {}
        data['images'] = [dict(full=p.photo.url,
                               thumb=get_thumbnail(p.photo, "120x120",
                                                   crop="center").url)
                          for p in obj.photos.all()]

        return mark_safe(
            render_to_string("admin/wallposts/mediawallpost_gallery.html", data)
        )

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


class TextWallpostAdmin(BaseWallpostAdmin):
    readonly_fields = ('ip_address', 'created', 'deleted', 'view_online', 'donation_link')
    search_fields = ('text', 'author__first_name', 'author__last_name')
    list_display = ('created', 'author', 'content_type', 'text', 'deleted')
    raw_id_fields = ('author', 'editor', 'donation')
    fields = readonly_fields + ('text', 'author', 'editor', 'pinned')
    exclude = ('object_id', 'content_type')

    ordering = ('-created',)

    inlines = (ReactionInline, )

    def donation_link(self, obj):
        if obj.donation:
            link = reverse('admin:funding_donation_change', args=(obj.donation.id,))
            return format_html(
                u"<a href='{}'>{}</a>",
                link, obj.donation
            )

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


class SystemWallpostAdmin(BaseWallpostAdmin):
    base_model = SystemWallpost
    readonly_fields = ('ip_address', 'created', 'view_online', 'content_type', 'related_type',
                       'donation_link', 'related_id', 'object_id')
    fields = readonly_fields + ('author', 'donation', 'text', 'pinned')
    list_display = ('created', 'author', 'content_type', 'related_type', 'text', 'deleted')
    raw_id_fields = ('author', 'editor', 'donation')
    ordering = ('-created',)
    exclude = ('object_id', 'content_type')

    inlines = (ReactionInline, )

    def donation_link(self, obj):
        if obj.donation:
            link = reverse('admin:funding_donation_change', args=(obj.donation.id,))
            return format_html(
                u"<a href='{}'>{}</a>",
                link, obj.donation
            )

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


class WallpostParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = Wallpost
    list_display = ('created', 'author', 'content_type', 'text', 'type', 'deleted')
    fields = ('title', 'text', 'author', 'ip_address', 'pinned')
    list_filter = ('created', ('content_type', admin.RelatedOnlyFieldListFilter),)
    ordering = ('-created',)
    search_fields = (
        'textwallpost__text', 'mediawallpost__text',
        'author__username', 'author__email',
        'author__first_name', 'author__last_name', 'ip_address'
    )
    child_models = (
        (MediaWallpost, MediaWallpostAdmin),
        (TextWallpost, TextWallpostAdmin),
        (SystemWallpost, SystemWallpostAdmin),
    )

    def type(self, obj):
        return obj.get_real_instance_class().__name__

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()

    def text(self, obj):
        text = '-empty-'
        try:
            text = obj.systemwallpost.text
        except SystemWallpost.DoesNotExist:
            pass
        try:
            text = obj.textwallpost.text
        except TextWallpost.DoesNotExist:
            pass
        try:
            text = obj.mediawallpost.text
        except MediaWallpost.DoesNotExist:
            pass
        if len(text) > 40:
            return format_html(u'{}&hellip;', text[:38])
        return text


admin.site.register(Wallpost, WallpostParentAdmin)
admin.site.register(MediaWallpost, MediaWallpostAdmin)
admin.site.register(TextWallpost, TextWallpostAdmin)
admin.site.register(SystemWallpost, SystemWallpostAdmin)


class ReactionAdmin(admin.ModelAdmin):
    # created and updated are auto-set fields. author, editor and ip_address are auto-set on save.
    readonly_fields = ('parent_url', 'created', 'updated', 'author',
                       'editor', 'ip_address')
    list_display = ('author_full_name', 'created', 'updated',
                    'deleted', 'ip_address')
    date_hierarchy = 'created'
    ordering = ('-created',)
    raw_id_fields = ('author', 'editor', 'wallpost')
    search_fields = ('text', 'author__username', 'author__email',
                     'author__first_name', 'author__last_name', 'ip_address')

    fields = ('text', 'parent_url', 'wallpost', 'deleted', 'created',
              'updated', 'author', 'editor', 'ip_address')

    def get_fieldsets(self, request, obj=None):
        """ Only show the relevant fields when adding a Reaction. """
        if obj:  # editing an existing object
            return super(ReactionAdmin, self).get_fieldsets(request, obj)
        return [(None, {'fields': ('wallpost', 'text')})]

    def author_full_name(self, obj):
        full_name = obj.author.get_full_name()
        if not full_name:
            return obj.author.username
        else:
            return full_name

    author_full_name.short_description = _('Author')

    def parent_url(self, obj):
        return obj.wallpost.content_object.get_absolute_url()

    parent_url.short_description = _('View update wall')

    def save_model(self, request, obj, form, change):
        """ Set the author or editor (as required) and ip when saving the model. """
        set_author_editor_ip(request, obj)
        super(ReactionAdmin, self).save_model(request, obj, form, change)

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


admin.site.register(Reaction, ReactionAdmin)


class DonorWallpostInline(admin.TabularInline):

    model = Wallpost
    readonly_fields = ('wallpost', 'donation', 'author', 'content_type', 'text')
    fields = readonly_fields
    extra = 0

    def text(self, obj):
        return obj.systemwallpost.text

    def wallpost(self, obj):
        url = reverse('admin:wallposts_wallpost_change', args=(obj.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj)


class WallpostInline(GenericTabularInline):

    model = Wallpost

    readonly_fields = ('wallpost', 'author', 'content_type', 'text')
    fields = readonly_fields
    extra = 0

    def text(self, obj):
        return obj.systemwallpost.text

    def wallpost(self, obj):
        url = reverse('admin:wallposts_wallpost_change', args=(obj.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj)

    def has_add_permission(self, request):
        return False
