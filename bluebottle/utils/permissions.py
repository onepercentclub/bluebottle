from rest_framework import permissions


class IsUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

    def has_permission(self, request, view):
        if request.data:
            user_id = request.data.get('user', None)
        else:
            user_id = request.query_params.get('user', None)
        return user_id == request.user.id


class IsOwner(permissions.BasePermission):
    """
    Allows access only to obj owner.
    """

    owner_field = 'owner'

    def has_object_permission(self, request, view, obj):
        return request.user == getattr(obj, self.owner_field, None)


class BaseResourcePermission(permissions.DjangoModelPermissions):
    authenticated_user_only = True

    perms_map = {
        'GET': ['%(app_label)s.api_view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_%(model_name)s'],
    }

    def has_permissions(self, request, method, model):
        return all(
            request.user.has_perm(perm) for perm in
            self.get_required_permissions(method, model)
        )

    def get_permissions(self, request, model):
        return {
            'change project': self.has_permissions(request, 'PUT', model),
            'delete project': self.has_permissions(request, 'DELETE', model),
            'view project': self.has_permissions(request, 'GET', model),
        }


class ResourcePermissions(BaseResourcePermission):
    authenticated_users_only = False
