from bluebottle.projects.permissions import RelatedResourceOwnerPermission, BasePermission
from bluebottle.tasks.models import Task


class RelatedManagementOrReadOnlyPermission(RelatedResourceOwnerPermission):
    """
    Is the current user either Project.owner, Project.task_management, Project.promoter
    or Task.project.owner, Task.project.task_management, Task.project.promoter
    or Fundraiser.owner
    """
    def has_parent_permission(self, action, user, parent, model=None):
        if isinstance(parent, Task):
            parent = parent.project

        return user in [
            getattr(parent, 'owner', None),
            getattr(parent, 'task_manager', None),
            getattr(parent, 'promoter', None)
        ]

    def has_object_action_permission(self, action, user, obj):
        if not any([
            obj.share_with_linkedin,
            obj.share_with_twitter,
            obj.share_with_facebook,
            obj.email_followers
        ]):
            return True

        return self.has_parent_permission(action, user, obj.parent)

    def has_action_permission(self, action, user, model):
        return True


class WallpostOwnerPermission(BasePermission):
    """
    Custom permission to only adding a photo to mediawallpost author.
    Model instances are expected to include an `mediawallpost` attribute.
    Also check if the user is the photo (or other object) author.
    """
    def has_parent_permission(self, action, user, parent, model=None):
        return parent.owner == user

    def has_object_action_permission(self, action, user, obj):
        return (
            not obj.parent or self.has_parent_permission(self, action, user, obj.parent)
        )

    def has_action_permission(self, action, user, model):
        return True


class DonationOwnerPermission(BasePermission):
    """
    Custom permission to only adding a photo to mediawallpost author.
    Model instances are expected to include an `mediawallpost` attribute.
    Also check if the user is the photo (or other object) author.
    """
    def has_object_action_permission(self, action, user, obj):
        return (
            obj.donation.user == user if obj.donation else True
        )

    def has_action_permission(self, action, user, model):
        return True
