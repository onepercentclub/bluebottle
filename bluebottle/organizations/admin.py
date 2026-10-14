from builtins import str

from django import forms
from django.contrib import admin
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from bluebottle.activities.models import Activity
from bluebottle.cms.models import SitePlatformSettings
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
        url = reverse('admin:{0}_{1}_change'.format(obj._meta.app_label,
                                                    obj._meta.model_name),
                      args=[obj.id])
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.title)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrganizationContact)
class OrganizationContactAdmin(admin.ModelAdmin):
    inlines = (OrganizationInitiativeInline, )
    fields = ('name', 'email', 'phone', )
    list_display = ('name', 'email', 'phone', )

    export_fields = [
        ('name', 'name'),
        ('email', 'email'),
        ('phone', 'Phone Number'),
    ]

    actions = (export_as_csv_action(fields=export_fields), )


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
    inlines = (OrganizationInitiativeInline, OrganizationActivityInline)
    form = OrganizationForm
    ordering = ('name',)
    view_on_site = True
    readonly_fields = ('color_contrast_panel',)

    class Media:
        css = {
            'all': ('admin/css/platform_color_contrast.css',)
        }
        js = ('admin/js/organization_color_contrast.js',)

    list_display = ('name', 'website', 'verified', 'created')
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

    def color_contrast_panel(self, obj):
        platform = SitePlatformSettings.load()
        return mark_safe(render_to_string(
            'admin/organizations/color_contrast_panel.html',
            {'accessible': platform.accessible_colours},
        ))

    color_contrast_panel.short_description = _('Colour preview')

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

    actions = (export_as_csv_action(fields=export_fields), )
