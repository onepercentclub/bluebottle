from bluebottle.auth.forms import SetPermissionsConfirmationForm, ClearPermissionsConfirmationForm
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from django.contrib.auth.models import Group, Permission
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from permissions_widget.admin import NewGroupAdmin as PermissionGroupAdmin

from bluebottle.auth.settngs import cms_permissions


class NewGroupAdmin(PermissionGroupAdmin):

    def get_urls(self):
        urls = super(NewGroupAdmin, self).get_urls()
        set_permission_urls = [
            url(r'^(?P<pk>\d+)/set-cms-permissions/$',
                self.admin_site.admin_view(self.set_cms_permissions),
                name="set_cms_permissions"),
            url(r'^(?P<pk>\d+)/clear-cms-permissions/$',
                self.admin_site.admin_view(self.clear_cms_permissions),
                name="clear_cms_permissions"),
        ]
        return set_permission_urls + urls

    @confirmation_form(
        SetPermissionsConfirmationForm,
        Group,
        'admin/auth/set_cms_permissions.html'
    )
    def set_cms_permissions(self, request, group):
        if not request.user.has_perm('auth.change_group'):
            return HttpResponseForbidden('Not allowed to change group')
        for perm in cms_permissions:
            app_label, codename = perm.split('.')
            permission = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
            if permission:
                group.permissions.add(permission)
        group.save()
        group_url = reverse('admin:auth_group_change', args=(group.id,))
        response = HttpResponseRedirect(group_url)
        return response

    @confirmation_form(
        ClearPermissionsConfirmationForm,
        Group,
        'admin/auth/clear_cms_permissions.html'
    )
    def clear_cms_permissions(self, request, group=None):
        if not request.user.has_perm('auth.change_group'):
            return HttpResponseForbidden('Not allowed to change group')

        for perm in cms_permissions:
            app_label, codename = perm.split('.')
            permission = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
            if permission:
                group.permissions.remove(permission)
        group.save()
        group_url = reverse('admin:auth_group_change', args=(group.id,))
        response = HttpResponseRedirect(group_url)
        return response


admin.site.unregister(Group)
admin.site.register(Group, NewGroupAdmin)
