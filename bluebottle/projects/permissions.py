from rest_framework import permissions

from bluebottle.utils.utils import get_class
from bluebottle.utils.permissions import RelatedResourceOwnerPermission


class RelatedProjectOwnerPermission(RelatedResourceOwnerPermission):
    parent_class = 'bluebottle.projects.models.Project'

    def get_parent_from_request(self, request):
        project_slug = request.data['project']
        cls = get_class(self.parent_class)
        try:
            parent = cls.objects.get(slug=project_slug)
        except cls.DoesNotExist:
            return None

        return parent


class IsEditableOrReadOnly():
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.status.editable

    def has_permission(self, request, view):
        return True
