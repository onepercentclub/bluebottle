from rest_framework import permissions

from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class MemberOrTaskOwnerResourcePermission(RelatedResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            if obj.member == user:
                return True

            parent = obj.task

        return parent.owner == user


class ActiveProjectOrReadOnlyPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        if action in permissions.SAFE_METHODS:
            return True

        return parent.project.status.slug == 'campaign'

    def has_action_permission(self, action, user, model):
        return True


class ResumePermission(BasePermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if user.has_perm('tasks.api_read_taskmember_resume'):
            return True

        if user.has_perm('tasks.api_read_own_taskmember_resume'):
            if obj:
                if obj.member == user:
                    return True

                parent = obj.task

            return parent.owner == user

        return False

    def has_action_permission(self, action, user, model):
        return True
