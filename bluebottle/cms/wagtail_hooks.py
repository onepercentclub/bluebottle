from django.conf.urls import include, url
from django.core import urlresolvers

from wagtail.wagtailcore import hooks
from django.contrib.staticfiles.templatetags.staticfiles import static
from bluebottle.donations.models import Donation
from wagtail.contrib.modeladmin.helpers import ButtonHelper

from bluebottle.members.models import Member
from bluebottle.tasks.models import Task
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.utils import quote

from bluebottle.projects.models import Project
from bluebottle.votes.models import Vote
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, ModelAdminGroup)

from bluebottle.geo.models import Location
from bluebottle.cms import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^cms/', include(admin_urls, namespace='cms', app_name='cms')),
    ]


@hooks.register('insert_editor_js')
def editor_js():
    return """
        <script src="{}"></script>
        <script>
            window.chooserUrls.projectChooser = '{}';
        </script>
    """.format(
        static('cms/js/project-chooser.js'), urlresolvers.reverse('cms:project_chooser')
    )


class ProjectThemeFilter(admin.SimpleListFilter):
    title = _('Theme')
    parameter_name = 'theme'

    def lookups(self, request, model_admin):
        themes = [obj.theme for obj in
                  model_admin.model.objects.order_by('theme__name').distinct(
                      'theme__name').exclude(theme__isnull=True).all()]
        return [(theme.id, _(theme.name)) for theme in themes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(theme__id__exact=self.value())
        else:
            return queryset


class LocationFilter(admin.SimpleListFilter):
    title = _('Location')
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        locations = [obj.location for obj in model_admin.model.objects.order_by(
            'location__name').distinct('location__name').exclude(
            location__isnull=True).all()]
        return [(loc.id, loc.name) for loc in locations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(location__id__exact=self.value())
        else:
            return queryset


class EditOnlyButtonHelper(ButtonHelper):

    def edit_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('edit', quote(pk)),
            'label': _('Edit / View'),
            'classname': cn,
            'title': _('Edit this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=[], classnames_add=[],
                            classnames_exclude=[]):
        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []

        btns.append(
            self.edit_button(pk, classnames_add, classnames_exclude)
        )
        return btns


class ProjectButtonHelper(ButtonHelper):

    def edit_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('edit', quote(pk)),
            'label': _('Edit / View'),
            'classname': cn,
            'title': _('Edit this %s') % self.verbose_name,
        }

    def reject_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            # 'url': self.url_helper.get_action_url('reject', quote(pk)),
            'label': _('Reject'),
            'classname': cn,
            'title': _('Reject this %s') % self.verbose_name,
        }

    def terminate_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            # 'url': self.url_helper.get_action_url('reject', quote(pk)),
            'label': _('Terminate'),
            'classname': cn,
            'title': _('Terminate this %s') % self.verbose_name,
        }

    def accept_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.inspect_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            # 'url': self.url_helper.get_action_url('reject', quote(pk)),
            'label': _('Accept'),
            'classname': cn,
            'title': _('Move this %s to campaign phase') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=[], classnames_add=[],
                            classnames_exclude=[]):
        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []


        btns.append(
            self.edit_button(pk, classnames_add, classnames_exclude)
        )

        if obj.status.slug == 'plan-submitted':
            btns.append(
                self.accept_button(pk, classnames_add, classnames_exclude)
            )
            btns.append(
                self.reject_button(pk, classnames_add, classnames_exclude)
            )

        btns.append(
            self.terminate_button(pk, classnames_add, classnames_exclude)
        )
        return btns


class ProjectAdmin(ModelAdmin):
    model = Project
    menu_label = 'Projects'  # ditch this to use verbose_name_plural from model
    menu_icon = 'snippet'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    button_helper_class = ProjectButtonHelper

    export_fields = ['title', 'owner', 'created', 'status',
                     'deadline', 'amount_asked', 'amount_donated']

    def get_list_filter(self, request):
        filters = ('status', 'is_campaign', ProjectThemeFilter,
                   'country__subregion__region', 'project_type')

        # Only show Location column if there are any
        if Location.objects.count():
            filters +=  (LocationFilter, )
        return filters

    def get_list_display(self, request):
        fields = ('get_title_display', 'get_owner_display', 'created',
                  'status', 'is_campaign', 'deadline', 'donated_percentage')
        # Only show Location column if there are any
        if Location.objects.count():
            fields +=  ('location', )
        # Only show Vote_count column if there are any votes
        if Vote.objects.count():
            fields +=  ('vote_count', )
        return fields

    search_fields = ('title', 'owner__first_name', 'owner__last_name',
                     'organization__name')

    read_only_fields = ('owner', 'organization',)

    prepopulated_fields = {'slug': ('title',)}

    list_filter = ('country__subregion__region',)

    def get_title_display(self, obj):
        if len(obj.title) > 35:
            return u'<span title="{title}">{short_title} &hellip;</span>' \
                .format(title=escape(obj.title), short_title=obj.title[:45])
        return obj.title

    get_title_display.allow_tags = True
    get_title_display.admin_order_field = 'title'
    get_title_display.short_description = _('title')

    def get_owner_display(self, obj):
        return obj.owner.get_full_name()

    get_owner_display.admin_order_field = 'owner__last_name'
    get_owner_display.short_description = _('owner')

    def project_owner(self, obj):
        object = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(
            object._meta.app_label, object._meta.model_name), args=[object.id])
        return "<a href='{0}'>{1}</a>".format(
            str(url), object.first_name + ' ' + object.last_name)

    project_owner.allow_tags = True


modeladmin_register(ProjectAdmin)


class TaskAdmin(ModelAdmin):
    model = Task
    menu_icon = 'cog'
    menu_order = 200
    button_helper_class = EditOnlyButtonHelper
    list_display = ('title', 'project', 'status', 'deadline')

modeladmin_register(TaskAdmin)


class DonationAdmin(ModelAdmin):
    model = Donation
    menu_order = 300
    menu_icon = 'plus-inverse'
    button_helper_class = EditOnlyButtonHelper
    list_display = ('created', 'user', 'amount', 'project', 'status')

modeladmin_register(DonationAdmin)


class MemberAdmin(ModelAdmin):
    model = Member
    menu_order = 250
    menu_icon = 'group'
    button_helper_class = EditOnlyButtonHelper


modeladmin_register(MemberAdmin)


class ProjectAdminGroup(ModelAdminGroup):
    menu_label = 'More'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 500
    items = (ProjectAdmin, TaskAdmin)

modeladmin_register(ProjectAdminGroup)
