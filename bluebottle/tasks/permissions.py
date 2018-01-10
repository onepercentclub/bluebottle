from rest_framework import permissions

from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class TaskPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return (
            user == parent.task_manager or
            (action in permissions.SAFE_METHODS and user == parent.owner)
        )


class TaskMemberPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return (
            user == parent.project.task_manager or
            (action in permissions.SAFE_METHODS and user == parent.project.owner)
        )

    def has_object_action_permission(self, action, user, obj):
        return (
            self.has_parent_permission(action, user, obj.task) or
            user == obj.member
        )


class TaskManagerPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return user == parent.project.task_manager


class MemberOrTaskOwnerResourcePermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return parent.owner == user

    def has_object_action_permission(self, action, user, obj):
        return obj.member == user or self.has_parent_permission(action, user, obj.task)


class ActiveProjectOrReadOnlyPermission(BasePermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return parent.project.status.slug == 'campaign'

    def has_object_action_permission(self, action, user, obj):
        return (
            action in permissions.SAFE_METHODS or
            self.has_parent_permission(action, user, obj.parent)
        )

    def has_action_permission(self, action, user, model):
        return True


class ResumePermission(BasePermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return parent.owner == user

    def has_object_action_permission(self, action, user, obj):
        if user.has_perm('tasks.api_read_taskmember_resume'):
            return True

        if user.has_perm('tasks.api_read_own_taskmember_resume'):
            return obj.member == user or self.has_parent_permission(action, user, obj.task)

        return False

    def has_action_permission(self, action, user, model):
        return True
