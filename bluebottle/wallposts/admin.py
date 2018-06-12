import urlparse

from django.contrib import admin
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


class MediaWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost
    readonly_fields = ('ip_address', 'created', 'deleted', 'view_online', 'gallery', 'donation',
                       'share_with_facebook', 'share_with_twitter',
                       'share_with_linkedin', 'email_followers')
    fields = readonly_fields + ('text', 'author', 'editor')
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
                    urlparts = urlparse.urlparse(obj.video_url)
                    data['youtubeid'] = urlparse.parse_qs(urlparts.query)['v'][
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

    def view_online(self, obj):
        if obj.content_object is None:
            return _(u'The project this post belongs to has been deleted')

        if obj.content_type.name == 'project':
            return format_html(
                u'<a href="/projects/{}">{}</a>',
                obj.content_object.slug, obj.content_object.title
            )
        if obj.content_type.name == 'task':
            if obj.content_object:
                return format_html(
                    u'<a href="/tasks/{}">{}</a>',
                    obj.content_object.id,
                    obj.content_object.title
                )
        if obj.content_type.name == 'fundraiser':
            return format_html(
                u'<a href="/fundraisers/{}">{}</a>',
                obj.content_object.id, obj.content_object.title
            )
        return '---'

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


class TextWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost
    readonly_fields = ('ip_address', 'created', 'deleted', 'posted_on', 'donation_link')
    search_fields = ('text', 'author__first_name', 'author__last_name')
    list_display = ('created', 'author', 'content_type', 'text', 'deleted')
    raw_id_fields = ('author', 'editor', 'donation')
    fields = readonly_fields + ('text', 'author', 'editor')
    exclude = ('object_id', 'content_type')

    ordering = ('-created',)

    inlines = (ReactionInline, )

    def posted_on(self, obj):
        type = obj.content_type.name
        type_name = unicode(obj.content_type).title()

        if type == 'task':
            url = reverse('admin:tasks_task_change',
                          args=(obj.content_object.id,))
        elif type == 'project':
            url = reverse('admin:projects_project_change',
                          args=(obj.content_object.id,))
        elif type == 'fundraiser':
            url = reverse('admin:fundraisers_fundraiser_change',
                          args=(obj.content_object.id,))
        else:
            return ''

        title = obj.content_object.title
        return format_html(
            u'{}: <a href="{}">{}</a>',
            type_name, url, title
        )

    def donation_link(self, obj):
        if obj.donation:
            link = reverse('admin:donations_donation_change', args=(obj.donation.id,))
            return format_html(
                u"<a href='{}'>{}</a>",
                link, obj.donation
            )

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


class SystemWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = SystemWallpost
    readonly_fields = ('ip_address', 'created', 'content_type', 'related_type',
                       'donation_link', 'project_link',
                       'related_id', 'object_id')
    fields = readonly_fields + ('author', 'donation', 'text')
    list_display = ('created', 'author', 'content_type', 'related_type', 'text', 'deleted')
    raw_id_fields = ('author', 'editor', 'donation')
    ordering = ('-created',)
    exclude = ('object_id', 'content_type')

    inlines = (ReactionInline, )

    def project_link(self, obj):
        if obj.donation:
            link = reverse('admin:projects_project_change', args=(obj.donation.project.id,))
            return format_html(
                u"<a href='{}'>{}</a>",
                link, obj.donation.project.title
            )
    project_link.short_description = _('Project link')

    def donation_link(self, obj):
        if obj.donation:
            link = reverse('admin:donations_donation_change', args=(obj.donation.id,))
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
    fields = ('title', 'text', 'author', 'ip_address')
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
            return format_html(text[:38] + '&hellip;')
        return text


admin.site.register(Wallpost, WallpostParentAdmin)
admin.site.register(MediaWallpost, MediaWallpostAdmin)
admin.site.register(TextWallpost, TextWallpostAdmin)
admin.site.register(SystemWallpost, SystemWallpostAdmin)


class ReactionAdmin(admin.ModelAdmin):
    # created and updated are auto-set fields. author, editor and ip_address are auto-set on save.
    readonly_fields = ('project_url', 'created', 'updated', 'author',
                       'editor', 'ip_address')
    list_display = ('author_full_name', 'created', 'updated',
                    'deleted', 'ip_address')
    date_hierarchy = 'created'
    ordering = ('-created',)
    raw_id_fields = ('author', 'editor', 'wallpost')
    search_fields = ('text', 'author__username', 'author__email',
                     'author__first_name', 'author__last_name', 'ip_address')

    fields = ('text', 'project_url', 'wallpost', 'deleted', 'created',
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

    def project_url(self, obj):
        project = obj.wallpost.content_object
        if project.__class__.__name__ == 'Project':
            url = project.get_absolute_url()
            return format_html(
                u"<a href='{}'>{}</a>",
                str(url), project.title
            )
        return ''

    project_url.short_description = _('project link')

    def save_model(self, request, obj, form, change):
        """ Set the author or editor (as required) and ip when saving the model. """
        set_author_editor_ip(request, obj)
        super(ReactionAdmin, self).save_model(request, obj, form, change)

    def get_queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return self.model.objects_with_deleted.all()


admin.site.register(Reaction, ReactionAdmin)
