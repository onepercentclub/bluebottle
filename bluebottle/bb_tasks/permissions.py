from rest_framework import permissions

from bluebottle.utils.model_dispatcher import get_task_model, get_taskmember_model

BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()


class IsTaskAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows access only to task author.
    """

    def _get_task_from_request(self, request):
        if request.DATA:
            task_id = request.DATA.get('task', None)
        else:
            task_id = request.QUERY_PARAMS.get('task', None)
        if task_id:
            try:
                task = BB_TASK_MODEL.objects.get(pk=task_id)
            except BB_TASK_MODEL.DoesNotExist:
                return None
        else:
            return None
        return task

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for objects/lists related to a Task (e.g TaskMember).
        # Get the project form the request

        task = self._get_task_from_request(request)
        if task:
            return task.author == request.user
        return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        if isinstance(obj, BB_TASK_MODEL):
            return obj.author == request.user

        if isinstance(obj, BB_TASKMEMBER_MODEL):
            return obj.task.author == request.user


class IsMemberOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        return isinstance(obj, BB_TASKMEMBER_MODEL) and obj.member == request.user


class IsMemberOrAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, BB_TASKMEMBER_MODEL) and obj.task.author == request.user:
            return True

        if isinstance(obj, BB_TASKMEMBER_MODEL) and obj.member == request.user:
            return True

        return False

