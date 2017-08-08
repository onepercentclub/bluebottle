from rest_framework import permissions

from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.utils import get_class
from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedTaskOwnerPermission(RelatedResourceOwnerPermission):
    parent_class = 'bluebottle.tasks.models.Task'

    def get_parent_from_request(self, request):
        task_pk = request.data['task']
        cls = get_class(self.parent_class)
        try:
            parent = cls.objects.get(pk=task_pk)
        except cls.DoesNotExist:
            return None

        return parent


class MemberOrOwnerOrReadOnlyPermission(BasePermission):
    # TODO: Move this check to the serialiser
    def _time_spent_updated(self, request, task_member):
        if request.data:
            time_spent = request.data.get('time_spent', None)
            if time_spent and task_member.time_spent != time_spent:
                return True
        return False

    def has_object_method_permission(self, method, user, view, obj):
        if method in permissions.SAFE_METHODS:
            return True

	# FIXME: when this permission is used with the update task member
	#        then the obj is still a Task. Why?
        if isinstance(obj, TaskMember) and obj.task.owner == user:
            return True

        if isinstance(obj, TaskMember) and obj.member == user:
            # Task member cannot update his/her own time_spent
            if self._time_spent_updated(view.request, obj):
                return False
            return True

        return False

    def has_method_permission(self, method, user, view):
        return True


class ActiveProjectOrReadOnlyPermission(RelatedResourceOwnerPermission):
    parent_class = 'bluebottle.tasks.models.Task'

    def get_parent_from_request(self, request):
        if request.data:
            task_pk = request.data.get('task', None)
        else:
            task_pk = request.query_params.get('task', None)
        cls = get_class(self.parent_class)
        try:
            parent = cls.objects.get(pk=task_pk)
        except cls.DoesNotExist:
            return None

        return parent

    def has_method_permission(self, method, user, view):
        if method in permissions.SAFE_METHODS:
            return True

        task = self.get_parent_from_request(view.request)
        if task:
            return task.project.status.slug == 'campaign'
        return False
