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
