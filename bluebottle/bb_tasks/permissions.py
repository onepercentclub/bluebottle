from rest_framework import permissions

from bluebottle.tasks.models import Task, TaskMember


class IsTaskAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows access only to task author.
    """

    def _get_task_from_request(self, request):
        if request.data:
            task_id = request.data.get('task', None)
        else:
            task_id = request.query_params.get('task', None)
        if task_id:
            try:
                task = Task.objects.get(pk=task_id)
            except Task.DoesNotExist:
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
        if isinstance(obj, Task):
            return obj.author == request.user

        if isinstance(obj, TaskMember):
            return obj.task.author == request.user


class IsMemberOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Test for project model object-level permissions.
        return isinstance(obj,
                          TaskMember) and obj.member == request.user


class IsMemberOrAuthorOrReadOnly(permissions.BasePermission):

    def _time_spent_updated(self, request, task_member):
        if request.data:
            time_spent = request.data.get('time_spent', None)
            if time_spent and task_member.time_spent != time_spent:
                return True
        return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, TaskMember) and obj.task.author == request.user:
            return True

        if isinstance(obj, TaskMember) and obj.member == request.user:
            # Task member cannot update his/her own time_spent
            if self._time_spent_updated(request, obj):
                return False
            return True

        return False
