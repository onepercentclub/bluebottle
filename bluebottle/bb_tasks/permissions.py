from rest_framework import permissions

from bluebottle.tasks.models import TaskMember
from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedTaskOwnerPermission(RelatedResourceOwnerPermission):
    parent_class = 'bluebottle.tasks.models.Task'

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent
        return user == parent.owner


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
    def has_object_action_permission(self, action, user, obj=None, parent=None):
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
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        if action in permissions.SAFE_METHODS:
            return True

        return parent.project.status.slug == 'campaign'
