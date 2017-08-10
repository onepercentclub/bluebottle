from rest_framework import permissions

from bluebottle.utils.utils import get_class
from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedProjectOwnerPermission(RelatedResourceOwnerPermission):
    parent_class = 'bluebottle.projects.models.Project'

    def get_parent_from_request(self, request):
        if request.data:
            project_slug = request.data.get('project', None)
        else:
            project_slug = request.query_params.get('project', None)
        cls = get_class(self.parent_class)
        try:
            parent = cls.objects.get(slug=project_slug)
        except cls.DoesNotExist:
            return None

        return parent


class IsEditableOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return self.has_object_method_permission(request.method, None, view, obj)

    def has_object_method_permission(self, method, user, view, obj=None):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if method in permissions.SAFE_METHODS:
            return True

        return obj.status.editable

    def has_method_permission(self, method, user, view):
        return True
