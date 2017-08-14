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
    def has_object_action_permission(self, action, user, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if action in permissions.SAFE_METHODS:
            return True

        return obj.status.editable

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True


class IsProjectWallOwner(permissions.BasePermission):
    """
    Allows access only to project owner.
    """

    def has_object_permission(self, request, view, obj):
        return obj.mediawallpost.content_object.owner == request.user
