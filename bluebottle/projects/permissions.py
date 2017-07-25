from rest_framework import permissions

from bluebottle.utils.permissions import IsOwner as BaseIsOwner
from .models import Project


class IsOwner(BaseIsOwner):
    def get_parent_from_request(self, request):
        if request.data:
            project_slug = request.data.get('project', None)
        else:
            project_slug = request.query_params.get('project', None)
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                return None
        else:
            return None
        return project


class IsOwnerOrAdmin(IsOwner):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner or request.user.is_staff


class IsEditableOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return self.check_object_permission(request.method, None, view, obj)

    def check_object_permission(self, method, user, view, obj=None):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if method in permissions.SAFE_METHODS:
            return True

        return obj.status.editable

    def check_permission(self, method, user, view):
        pass
