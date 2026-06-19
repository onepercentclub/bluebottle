from bluebottle.utils.permissions import BasePermission


class ContentPageEditorPermission(BasePermission):
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


class ContentPageListPermission(BasePermission):
    def has_action_permission(self, action, user, model_cls):
        return user.is_authenticated and user.has_perm('pages.api_change_page')

    def has_object_action_permission(self, action, user, obj):
        return self.has_action_permission(action, user, obj.__class__)


class ContentBlockPermission(BasePermission):
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
                obj.page_id is not None
            )
        return False
