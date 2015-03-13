from bluebottle.utils.utils import set_author_editor_ip
from bluebottle.wallposts.models import SystemWallpost
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicParentModelAdmin)
from sorl.thumbnail.admin.compat import AdminImageMixin

from .models import (MediaWallpost, MediaWallpostPhoto, Reaction, TextWallpost,
                     Wallpost)


class MediaWallpostPhotoInline(AdminImageMixin, admin.StackedInline):
    model = MediaWallpostPhoto
    extra = 0
    raw_id_fields = ('author', 'editor')


class MediaWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost
    readonly_fields = ('ip_address', 'deleted')
    raw_id_fields = ('author', 'editor')
    list_display = ('created', 'view_online', 'get_text', 'video_url', 'photos', 'author')

    readonly_fields = ('view_online', )

    ordering = ('-created', )
    inlines = (MediaWallpostPhotoInline,)

    def get_text(self, obj):
        if len(obj.text) > 150:
            return u'<span title="{text}">{short_text} [...]</span>'.format(text=obj.text, short_text=obj.text[:145])
    get_text.allow_tags = True

    def photos(self, obj):
        photos = MediaWallpostPhoto.objects.filter(mediawallpost=obj)
        if len(photos):
            return len(photos)
        return '-'

    def view_online(self, obj):
        if obj.content_type.name == 'project':
            return u'<a href="/go/projects/{slug}">{title}</a>'.format(slug=obj.content_object.slug, title=obj.content_object.title)
        if obj.content_type.name == 'task':
            return u'<a href="/go/projects/{slug}/tasks/{task_id}">{title}</a>'.format(slug=obj.content_object.project.slug, task_id=obj.content_object.id, title=obj.content_object.project.title)
        if obj.content_type.name == 'fundraiser':
            return u'<a href="/go/fundraisers/{id}">{title}</a>'.format(id=obj.content_object.id, title=obj.content_object.title)
        return '---'

    view_online.allow_tags = True



class TextWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost
    readonly_fields = ('ip_address', 'deleted')
    list_display = ('created', 'author', 'content_type', 'text')
    raw_id_fields = ('author', 'editor')
    ordering =  ('-created', )
    readonly_fields = ('wallpost_link', )

    def wallpost_link(self, obj):
        if str(obj.content_type)  == 'task':
            task = obj.content_object
            url = '/#!/projects/{project_slug}/tasks/{task_id}'.format(
                            project_slug = task.project.slug,
                            task_id = task.id,
                            )
            return "<a href='%s'>%s</a>" % (str(url), task.title)
        # Assume it's a Project wallpost
        return u'<a href="/go/projects/{slug}">{title}</a>'.format(slug=obj.content_object.slug, title=obj.content_object.title)

    wallpost_link.allow_tags = True



class SystemWallpostAdmin(PolymorphicChildModelAdmin):
    base_model = Wallpost
    readonly_fields = ('ip_address', 'deleted')
    list_display = ('created', 'author', 'content_type', 'related_type', 'text')
    raw_id_fields = ('author', 'editor')
    ordering = ('-created', )


class WallpostParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = Wallpost
    list_display = ('created', 'author', 'content_type')
    ordering = ('-created', )
    child_models = (
        (MediaWallpost, MediaWallpostAdmin),
        (TextWallpost, TextWallpostAdmin),
        (SystemWallpost, SystemWallpostAdmin),
    )

# Only the parent needs to be registered:
admin.site.register(Wallpost, WallpostParentAdmin)

# So why you are also registering the child?
admin.site.register(MediaWallpost, MediaWallpostAdmin)
admin.site.register(TextWallpost, TextWallpostAdmin)
admin.site.register(SystemWallpost, SystemWallpostAdmin)


class ReactionAdmin(admin.ModelAdmin):
    # created and updated are auto-set fields. author, editor and ip_address are auto-set on save.
    readonly_fields = ('project_url', 'created', 'updated', 'author', 'editor', 'ip_address')
    list_display = ('author_full_name', 'created', 'updated', 'deleted', 'ip_address')
    list_filter = ('created', 'updated', 'deleted')
    date_hierarchy = 'created'
    ordering = ('-created',)
    raw_id_fields = ('author', 'editor')
    search_fields = ('text', 'author__username', 'author__email', 'author__first_name', 'author__last_name', 'ip_address')

    fields = ('text', 'project_url', 'wallpost', 'deleted', 'created', 'updated', 'author', 'editor', 'ip_address')

    def get_fieldsets(self, request, obj=None):
        """ Only show the relevant fields when adding a Reaction. """
        if obj: # editing an existing object
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
            url = project.get_absolute_frontend_url()
            return "<a href='%s'>%s</a>" % (str(url), project.title)
        return ''

    project_url.allow_tags = True
    project_url.short_description = _('project link')

    def save_model(self, request, obj, form, change):
        """ Set the author or editor (as required) and ip when saving the model. """
        set_author_editor_ip(request, obj)
        super(ReactionAdmin, self).save_model(request, obj, form, change)

    def queryset(self, request):
        """ The Admin needs to show all the Reactions. """
        return Reaction.objects_with_deleted.all()

admin.site.register(Reaction, ReactionAdmin)
