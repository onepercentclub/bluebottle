from django.contrib.auth.models import Group, Permission


class AnonymousAuthenticationBackend(object):
    """
    Make anonymous users part of a permission group.

    If users are not authenticated, we assume that they are part of a permission
    group `group_name` ('Anonymous' by default)
    """
    group_name = 'Anonymous'

    def get_user(self, user_id):
        return None

    def authenticate(self, *args, **kwargs):
        return None

    def has_perm(self, user, perm, obj):
        """
        Check if `user` has permission `perm`

        If the user is not authenticated, check if the permission is part of
        the anonymous group.
        """
        if user.is_authenticated:
            return False

        try:
            group = Group.objects.get(name=self.group_name)
            (app_label, codename) = perm.split('.')

            group.permissions.get(codename=codename, content_type__app_label=app_label)
            return True
        except (Permission.DoesNotExist, Group.DoesNotExist):
            return False

    def get_user(self, user_id):
        return None
