from builtins import str

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from bluebottle.activities.models import Activity
from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.models import Accept, Event, Follow
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.cms.utils.color_contrast import render_solid_preview
from bluebottle.initiatives.models import Initiative
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.translations.admin import TranslatableLabelAdminMixin
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.widgets import SecureAdminURLFieldWidget


class OrganizationInitiativeInline(admin.TabularInline):
    model = Initiative
    readonly_fields = ('initiative_url', 'owner', 'status')
    fields = ('initiative_url', 'owner', 'status')
    extra = 0

    def initiative_url(self, obj):
        url = reverse('admin:{0}_{1}_change'.format(obj._meta.app_label,
                                                    obj._meta.model_name),
                      args=[obj.id])
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.title)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationActivityInline(admin.TabularInline):
    model = Activity
    readonly_fields = ('activity_url', 'owner', 'status')
    fields = ('activity_url', 'owner', 'status')
    extra = 0
    fk_name = 'organization'

    def activity_url(self, obj):
        url = reverse(
            'admin:{0}_{1}_change'.format(
                obj._meta.app_label,
                obj._meta.model_name
            ),
            args=[obj.id]
        )
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.title)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationLinkedActivityInline(admin.TabularInline):
    model = LinkedActivity
    verbose_name_plural = _('Linked activities')
    readonly_fields = ('activity_url', 'activity_type', 'status')
    fields = ('activity_url', 'activity_type', 'status')
    fk_name = 'host_organization'
    extra = 0

    def activity_url(self, obj):
        model = obj.get_real_instance_class()
        url = reverse(
            'admin:{0}_{1}_change'.format(model._meta.app_label, model._meta.model_name),
            args=[obj.id]
        )
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.title)

    activity_url.short_description = _('Title')

    def activity_type(self, obj):
        return obj.get_real_instance_class().activity_type

    activity_type.short_description = _('Type')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrganizationContact)
class OrganizationContactAdmin(admin.ModelAdmin):
    inlines = (OrganizationInitiativeInline,)
    fields = ('name', 'email', 'phone',)
    list_display = ('name', 'email', 'phone',)

    export_fields = [
        ('name', 'name'),
        ('email', 'email'),
        ('phone', 'Phone Number'),
    ]

    actions = (export_as_csv_action(fields=export_fields),)


class OrganizationForm(TranslatableModelForm):
    website = forms.CharField(required=True)

    class Meta:
        model = Organization
        fields = '__all__'


@admin.register(Organization)
class OrganizationAdmin(
    TranslatableLabelAdminMixin,
    TranslatableAdmin,
):
    inlines = (
        OrganizationInitiativeInline, OrganizationActivityInline, OrganizationLinkedActivityInline
    )
    form = OrganizationForm
    ordering = ('name',)
    view_on_site = True
    readonly_fields = (
        'color_contrast_panel',
        'connect_local_actor', 'connect_supplier', 'connect_consumer',
        'connect_shared_activities', 'connect_adopted_activities',
        'connect_partner_activities',
    )

    connect_fields = (
        'connect_local_actor', 'connect_supplier', 'connect_consumer',
        'connect_shared_activities', 'connect_adopted_activities',
        'connect_partner_activities',
    )

    class Media:
        css = {
            'all': ('admin/css/platform_color_contrast.css',)
        }
        js = ('admin/js/color_contrast_base.js', 'admin/js/solid_color_contrast.js')

    list_display = ('name', 'activities_count', 'verified', 'created')
    list_filter = (
        ('initiatives__theme', admin.RelatedOnlyFieldListFilter),
        ('initiatives__location', admin.RelatedOnlyFieldListFilter),
    )
    fields = (
        'name', 'website', 'slogan', 'story', 'verified',
        'logo', 'image', 'color', 'color_contrast_panel',
    )
    search_fields = ('name',)
    export_fields = [
        ('name', 'name'),
        ('website', 'website'),
        ('created', 'created'),
    ]

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def activities_count(self, obj):
        if obj and obj.id:
            return obj.activities.count() + obj.linked_activities.count()
        return '-'

    def color_contrast_panel(self, obj):
        return render_solid_preview(
            'id_color',
            _('How this colour will look on the organisation page'),
        )

    color_contrast_panel.short_description = _('Colour preview')

    def get_fieldsets(self, request, obj=None):
        fieldsets = [[None, {'fields': self.get_fields(request, obj)}]]
        if obj and obj.pk and (
            self.get_connect_actor(obj) or SitePlatformSettings.load().is_sharing_activities
        ):
            fieldsets[0][0] = _('Main')
            fieldsets.append([_('GoodUp Connect'), {'fields': self.connect_fields}])
        return fieldsets

    def get_fields(self, request, obj=None):
        return [
            field for field in super().get_fields(request, obj)
            if field not in self.connect_fields
        ]

    def get_connect_actor(self, obj):
        return getattr(obj, 'activity_pub_organization', None)

    def connection_status(self, follows):
        follow = follows.first()
        if not follow:
            return _('No')
        if Accept.objects.filter(object=follow).exists():
            return _('Yes')
        return _('Yes, waiting for acceptance')

    def connect_local_actor(self, obj):
        actor = self.get_connect_actor(obj)
        if actor and actor.is_local:
            return _('Yes')
        return _('No')

    connect_local_actor.short_description = _('Local actor')

    def connect_supplier(self, obj):
        actor = self.get_connect_actor(obj)
        if not actor or actor.is_local:
            return _('No')
        return self.connection_status(Follow.objects.filter(object=actor))

    connect_supplier.short_description = _('Connected supplier')

    def connect_consumer(self, obj):
        actor = self.get_connect_actor(obj)
        if not actor or actor.is_local:
            return _('No')
        return self.connection_status(Follow.objects.filter(actor=actor))

    connect_consumer.short_description = _('Connected consumer')

    def connect_shared_activities(self, obj):
        actor = self.get_connect_actor(obj)
        if not actor:
            return 0
        return Event.objects.filter(create__actor=actor).distinct().count()

    connect_shared_activities.short_description = _('Activities shared via GoodUp Connect')

    def connect_adopted_activities(self, obj):
        return obj.hosted_activities.count() + obj.linked_activities.count()

    connect_adopted_activities.short_description = _('Adopted activities')

    def connect_partner_activities(self, obj):
        actor = self.get_connect_actor(obj)
        if not actor:
            return 0
        return Event.objects.filter(organization=actor).count()

    connect_partner_activities.short_description = _('Partner organisation of shared activities')

    def has_delete_permission(self, request, obj=None):
        settings = SitePlatformSettings.load()
        if obj and obj == settings.organization:
            return False
        return True

    def get_inline_instances(self, request, obj=None):
        """ Override get_inline_instances so that add form do not show inlines """
        if not obj:
            return []
        return super(OrganizationAdmin, self).get_inline_instances(request, obj)

    actions = (export_as_csv_action(fields=export_fields),)
