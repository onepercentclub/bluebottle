from rest_framework import permissions

from . import get_project_model

PROJECT_MODEL = get_project_model()


class IsProjectOwner(permissions.BasePermission):
    """
    Allows access only to project owner.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, PROJECT_MODEL):
            return obj.owner == request.user
        return obj.project.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Allows access only to project owner.
    """
    def has_object_permission(self, request, view, obj):
        # Test for project model object-level permissions.
        return isinstance(obj, PROJECT_MODEL) and obj.owner == request.user


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows access only to project owner.
    """
    def _get_project_from_request(self, request):
        if request.DATA:
            project_slug = request.DATA.get('project', None)
        else:
            project_slug = request.QUERY_PARAMS.get('project', None)
        if project_slug:
            try:
                project = PROJECT_MODEL.objects.get(slug=project_slug)
                return project
            except PROJECT_MODEL.DoesNotExist:
                return None
        else:
            return None

    def _get_project_from_view(self, view):
        project_pk = view.kwargs.get('pk', None)
        if project_pk:
            try:
                project = PROJECT_MODEL.objects.get(pk=project_pk)
                return project
            except PROJECT_MODEL.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for objects/lists related to a Project (e.g WallPosts).
        # Get the project from the request
        project = self._get_project_from_request(request)

        # Get the project from the view if it was not available in the request.
        if not project:
            project = self._get_project_from_view(view)
        return project and project.owner == request.user

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        if isinstance(obj, PROJECT_MODEL):
            return obj.owner == request.user
        else:
            return obj.project.owner == request.user
