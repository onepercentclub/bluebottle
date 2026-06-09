from bluebottle.cms.page_utils import get_page_for_block, is_editable_page_block
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.utils.permissions import BasePermission


class PageEditorPermission(BasePermission):
    def has_action_permission(self, action, user, model_cls):
        if action in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if action in ('PATCH', 'PUT', 'POST'):
            return user.is_authenticated and user.has_perm('pages.api_change_page')
        return False

    def has_object_action_permission(self, action, user, obj):
        if action in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if action in ('PATCH', 'PUT', 'POST'):
            return user.is_authenticated and user.has_perm('pages.api_change_page')
        return False


class PageListPermission(BasePermission):
    def has_action_permission(self, action, user, model_cls):
        return user.is_authenticated and user.has_perm('pages.api_change_page')

    def has_object_action_permission(self, action, user, obj):
        return self.has_action_permission(action, user, obj.__class__)


class PageBlockPermission(BasePermission):
    def has_action_permission(self, action, user, model_cls):
        if action in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if action in ('PATCH', 'PUT', 'DELETE'):
            return user.is_authenticated and user.has_perm('pages.api_change_page')
        return False

    def has_object_action_permission(self, action, user, obj):
        if action in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if action in ('PATCH', 'PUT', 'DELETE'):
            return (
                user.is_authenticated and
                user.has_perm('pages.api_change_page') and
                is_editable_page_block(obj) and
                get_page_for_block(obj) is not None
            )
        return False


class PlatformPagePermission(BasePermission):

    def has_permission(self, request, view):
        page = view.get_object()
        settings = MemberPlatformSettings.load()
        if (
            settings.closed
            and (not request.user or not request.user.is_authenticated)
            and page.slug == 'start'
        ):
            return False

        return True

    def __repr__(self):
        return 'PlatformPagePermission'
