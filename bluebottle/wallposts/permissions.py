from bluebottle.activities.models import Activity
from bluebottle.utils.permissions import RelatedResourceOwnerPermission, BasePermission
from bluebottle.wallposts.models import Wallpost


class RelatedManagementOrReadOnlyPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        if isinstance(parent, Activity):
            return user in [
                getattr(parent, 'owner', None),
                getattr(parent.initiative, 'owner', None),
                getattr(parent.initiative, 'promoter', None)
            ] + list(parent.initiative.activity_managers.all())

        return user in [
            getattr(parent, 'owner', None),
            getattr(parent, 'promoter', None)
        ] + list(parent.activity_managers.all())

    def has_object_action_permission(self, action, user, obj):
        if isinstance(obj, Wallpost) and not any([
            obj.share_with_linkedin,
            obj.share_with_twitter,
            obj.share_with_facebook,
            obj.email_followers
        ]):
            return True
        return self.has_parent_permission(action, user, obj.parent)

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
