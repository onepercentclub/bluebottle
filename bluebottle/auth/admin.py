from django.contrib.auth.models import Group, Permission
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from permissions_widget.admin import NewGroupAdmin as PermissionGroupAdmin

from bluebottle.auth.settngs import cms_permissions


class NewGroupAdmin(PermissionGroupAdmin):

    def get_urls(self):
        urls = super(NewGroupAdmin, self).get_urls()
        set_permission_urls = [
            url(r'^(?P<pk>\d+)/set-cms-permissions/$', self.set_cms_permissions, name="set_cms_permissions"),
            url(r'^(?P<pk>\d+)/clear-cms-permissions/$', self.clear_cms_permissions, name="clear_cms_permissions"),
        ]
        return set_permission_urls + urls

    def set_cms_permissions(self, request, pk=None):
        group = Group.objects.get(pk=pk)
        for perm in cms_permissions:
            app_label, codename = perm.split('.')
            permission = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
            if permission:
                group.permissions.add(permission)
        group.save()
        group_url = reverse('admin:auth_group_change', args=(group.id,))
        response = HttpResponseRedirect(group_url)
        return response

    def clear_cms_permissions(self, request, pk=None):
        group = Group.objects.get(pk=pk)
        for perm in cms_permissions:
            print "++++"
            app_label, codename = perm.split('.')
            permission = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
            if permission:
                group.permissions.remove(permission)
                print permission

        group.save()
        group_url = reverse('admin:auth_group_change', args=(group.id,))
        response = HttpResponseRedirect(group_url)
        return response


admin.site.unregister(Group)
admin.site.register(Group, NewGroupAdmin)
