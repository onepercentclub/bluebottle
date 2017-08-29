from rest_framework import permissions

from bluebottle.utils.permissions import RelatedResourceOwnerPermission


class TaskPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent):
        return (
            user == parent.task_manager or
            (action in permissions.SAFE_METHODS and user == parent.owner)
        )


class TaskMemberPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent):
        return (
            user == parent.project.task_manager or
            (action in permissions.SAFE_METHODS and user == parent.project.owner)
        )

    def has_object_action_permission(self, action, user, obj):
        return (
            self.has_parent_permission(action, user, obj.task) or
            user == obj.member
        )
