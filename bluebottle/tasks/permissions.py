from rest_framework import permissions

from bluebottle.utils.permissions import RelatedResourceOwnerPermission


class TaskPermission(RelatedResourceOwnerPermission):

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return (
            user == parent.task_manager or
            (action in permissions.SAFE_METHODS and user == parent.owner)
        )


class TaskMemberPermission(RelatedResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            project = obj.task.project
        elif parent:
            project = parent.project

        return (
            user == project.task_manager or
            (obj and obj.member == user) or
            (action in permissions.SAFE_METHODS and user == project.owner)
        )
