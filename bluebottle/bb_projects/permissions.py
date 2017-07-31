from rest_framework import permissions

from bluebottle.projects.models import Project


class ProjectPermissions(permissions.DjangoModelPermissions):
    authenticated_users_only = False

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


class ManageProjectPermissions(permissions.DjangoModelPermissions):
    authenticated_user_only = False

    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and request.user == obj.owner


class IsProjectOwner(permissions.BasePermission):
    """
    Permissions class used to allow access only to project owner.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return obj.owner == request.user
        return obj.project.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Allows access only to project owner.
    """
    def has_object_permission(self, request, view, obj):
        # Test for project model object-level permissions.
        return isinstance(obj, Project) and obj.owner == request.user


class IsEditableOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.status.editable


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissions class used to allow access only to project owner for those
    methods which are not specified in ``SAFE_METHODS``.

    Ideally, this will grant only-reading access for all users and restrict
    data changes permissions to the project owner only.
    """
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
        return project and project.owner == request.user

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        if isinstance(obj, Project):
            return obj.owner == request.user
        else:
            return obj.project.owner == request.user
