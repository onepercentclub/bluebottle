from builtins import str

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.initiatives.models import Initiative
from bluebottle.organizations.models import Organization, OrganizationContact
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


class OrganizationForm(forms.ModelForm):
    website = forms.CharField(required=True)

    class Meta:
        model = Organization
        fields = '__all__'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = (OrganizationInitiativeInline, )
    form = OrganizationForm

    list_display = ('name', 'website', 'created')
    list_filter = (
        ('initiatives__theme', admin.RelatedOnlyFieldListFilter),
        ('initiatives__location', admin.RelatedOnlyFieldListFilter),
    )
    fields = ('name', 'website', 'description', 'logo')
    search_fields = ('name',)
    export_fields = [
        ('name', 'name'),
        ('website', 'website'),
        ('created', 'created'),
    ]

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def get_inline_instances(self, request, obj=None):
        """ Override get_inline_instances so that add form do not show inlines """
        if not obj:
            return []
        return super(OrganizationAdmin, self).get_inline_instances(request, obj)

    actions = (export_as_csv_action(fields=export_fields), )
