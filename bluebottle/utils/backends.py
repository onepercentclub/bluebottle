from builtins import object

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group, Permission


class BlueBottleModelBackend(ModelBackend):
    """
    Same as Django's model backend, but an email that matches more than one
    member does not raise. The member whose password matches is used, so a
    duplicate row with a different password does not lock the real account out.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
        if username is None or password is None:
            return
        if isinstance(username, int):
            try:
                user = user_model._default_manager.get_by_natural_key(username)
            except user_model.DoesNotExist:
                user_model().set_password(password)
                return
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            return

        matches = user_model._default_manager.matching_emails(username)
        if not matches:
            user_model().set_password(password)
            return
        for user in matches:
            if user.check_password(password) and self.user_can_authenticate(user):
                user_model._default_manager.log_duplicate_members(username, matches, user)
                return user
        user_model._default_manager.log_duplicate_members(
            username,
            matches,
            user_model._default_manager.choose_duplicate_member(matches),
        )


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
