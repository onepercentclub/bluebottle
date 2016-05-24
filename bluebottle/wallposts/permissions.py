from rest_framework import permissions

from bluebottle.fundraisers.models import Fundraiser
from bluebottle.tasks.models import Task
from bluebottle.projects.models import Project


from .models import MediaWallpost


class CanEmailFollowers(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # If followers will be emailed then check the request user
        # has permissions, eg they are the owner / author of the
        # parent object (project, task, fundraiser).
        if obj.email_followers:
            parent_obj = obj.content_object

            if isinstance(parent_obj, Project) or \
               isinstance(parent_obj, Fundraiser):
                return parent_obj.owner == self.request.user
            elif isinstance(parent_obj, Task):
                return parent_obj.author == self.request.user
        else:
          return True


# TODO: Add write permission for 1%CREW / Assistants.
class IsConnectedWallpostAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only adding a photo to mediawallpost author.
    Model instances are expected to include an `mediawallpost` attribute.
    Also check if the user is the photo (or other object) author.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always
        # allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Look for the Wallpost that the user is trying to set.
        mediawallpost_id = request.data.get('mediawallpost', None)
        if mediawallpost_id:
            try:
                mediawallpost = MediaWallpost.objects.get(pk=mediawallpost_id)
            except MediaWallpost.DoesNotExist:
                return False
        else:
            # If the user isn't trying to set a wallpost, than we can carry on.
            return True

        if mediawallpost.author == request.user:
            return True

        return False
