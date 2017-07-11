from django.contrib.auth.models import Group, Permission


class AnonymousAuthenticationBackend(object):
    group_name = 'Anonymous'

    def has_perm(self, user, perm, obj):
        group = Group.objects.get(name=self.group_name)
        (app_label, codename) = perm.split('.')

        try:
            group.permissions.get(codename=codename, content_type__app_label=app_label)
            return True
        except Permission.DoesNotExist:
            return False
