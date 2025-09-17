from builtins import str

from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import re_path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Organization as PubOrganization
from bluebottle.initiatives.models import Initiative
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.utils import get_current_host
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

    list_display = ('name', 'website', 'verified', 'created')
    list_filter = (
        ('initiatives__theme', admin.RelatedOnlyFieldListFilter),
        ('initiatives__location', admin.RelatedOnlyFieldListFilter),
    )
    readonly_fields = ['pub_organization']
    fields = ('name', 'website', 'description', 'verified', 'logo', 'pub_organization')
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

    def pub_organization(self, obj):
        try:
            if obj.puborganization.url:
                pub_url = obj.puborganization.url
            else:
                pub_url = get_current_host() + reverse("json-ld:organization", args=(obj.puborganization.pk,))
            url = reverse("admin:activity_pub_organization_change", args=(obj.puborganization.pk,))
            return format_html(
                '<a href="{}">{}</a>&nbsp;&nbsp;<i>{}</i>',
                url,
                _("Go to ActivityPub object"),
                pub_url
            )
        except Organization.puborganization.RelatedObjectDoesNotExist:
            url = reverse('admin:organizations_organization_create_pub_organization', kwargs={'pk': obj.id})
            return format_html(
                "<a href='{}'>{}</a>",
                url, _("Create ActivityPub Organization"),
            )

    def get_urls(self):
        urls = super(OrganizationAdmin, self).get_urls()

        extra_urls = [
            re_path(
                r'^create-pub-organization/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.create_pub_organization),
                name='organizations_organization_create_pub_organization'
            ),
        ]
        return extra_urls + urls

    def create_pub_organization(self, request, pk):
        organization = Organization.objects.get(pk=pk)
        self.organization = PubOrganization.objects.from_model(organization)
        message = _('Organisation {name} now has a ActivityPub Organization.').format(name=organization.name)
        self.message_user(request, message)
        return HttpResponseRedirect(reverse('admin:organizations_organization_change', args=(organization.id,)))
