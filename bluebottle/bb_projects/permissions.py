from rest_framework import permissions

from bluebottle.projects.models import Project


class IsProjectOwner(permissions.BasePermission):
    """
    Permissions class used to allow access only to project owner.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return obj.owner == request.user
        return obj.project.owner == request.user


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissions class used to allow access only to project owner for those
    methods which are not specified in ``SAFE_METHODS``.

    Ideally, this will grant only-reading access for all users and restrict
    data changes permissions to the project owner only.
    """
    owner_field = 'owner'

    def _get_project_from_request(self, request):
        if request.data:
            project_slug = request.data.get('project', None)
        else:
            project_slug = request.query_params.get('project', None)
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
                return project
            except Project.\
                    DoesNotExist:
                return None
        else:
            return None

    def _get_project_from_view(self, view):
        project_pk = view.kwargs.get('pk', None)
        if project_pk:
            try:
                project = Project.objects.get(pk=project_pk)
                return project
            except Project.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests. However, DELETE is a special case
        # because it needs to reference the object which is going to be deleted
        # and thus check that object permissions, so we'll let it pass also.
        if request.method in permissions.SAFE_METHODS or request.method == 'DELETE':
            return True

        # Test for objects/lists related to a Project (e.g Wallposts).
        # Get the project from the request
        project = self._get_project_from_request(request)

        # Get the project from the view if it was not available in the request.
        if not project:
            project = self._get_project_from_view(view)
        return project and getattr(project, self.owner_field) == request.user

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        if isinstance(obj, Project):
            return getattr(obj, self.owner_field) == request.user
        else:
            return getattr(obj.project, self.owner_field) == request.user


class IsProjectTaskManagerOrReadOnly(IsProjectOwnerOrReadOnly):
    """
    Same as IsProjectOwnerOrReadOnly but uses 'task_manager' field.
    """
    owner_field = 'task_manager'
