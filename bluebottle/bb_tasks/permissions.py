from rest_framework import permissions

from bluebottle.tasks.models import TaskMember
from bluebottle.utils.utils import get_class
from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedTaskOwnerPermission(RelatedResourceOwnerPermission):
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

    def has_object_action_permission(self, action, user, obj):
        return user == obj.owner


class TaskMemberTimeSpentPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.member == request.user and request.data:
            time_spent = request.data.get('time_spent', None)
            if time_spent and obj.time_spent != time_spent:
                return False

        return True

    def has_permission(self, request, view):
        return True

    def has_action_permission(self, action, user, model_cls, parent=None):
        pass


class MemberOrTaskOwnerOrReadOnlyPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        if action in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, TaskMember) and obj.task.owner == user:
            return True

        if isinstance(obj, TaskMember) and obj.member == user:
            return True

        return False

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True


class MemberOrTaskOwnerOrAdminPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        # FIXME: when this permission is used with the update task member
        #        then the obj is still a Task. Why?
        if isinstance(obj, TaskMember):
            return (
                obj.task.owner == user or
                obj.member == user or
                user.is_staff
            )

        return False

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True


class ActiveProjectOrReadOnlyPermission(RelatedTaskOwnerPermission):
    def has_method_object_permission(self, action, user, obj):
        pass

    def has_action_permission(self, action, user, model_cls, parent=None):
        if action in permissions.SAFE_METHODS:
            return True

        if parent:
            return parent.project.status.slug == 'campaign'
        return False
