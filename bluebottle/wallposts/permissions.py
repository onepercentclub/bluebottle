from rest_framework import permissions

from bluebottle.fundraisers.models import Fundraiser
from bluebottle.projects.permissions import RelatedProjectOwnerPermission
from bluebottle.tasks.models import Task
from bluebottle.projects.models import Project

from .models import MediaWallpost


class RelatedManagementOrReadOnlyPermission(RelatedProjectOwnerPermission):
    """
    Is the current user either Project.owner, Project.task_management, Project.promoter
    or Task.project.owner, Task.project.task_management, Task.project.promoter
    or Fundraiser.owner
    """
    parent_class = 'bluebottle.projects.models.Project'

    def get_parent_from_request(self, request):
        parent_id = request.data['parent_id']
        parent_type = request.data['parent_type']
        if parent_type == 'project':
            try:
                return Project.objects.get(slug=parent_id)
            except Project.DoesNotExist:
                return Project.objects.none()
        if parent_type == 'fundraiser':
            try:
                return Fundraiser.objects.get(id=parent_id)
            except Fundraiser.DoesNotExist:
                return Fundraiser.objects.none()
        if parent_type == 'task':
            try:
                return Task.objects.get(id=parent_id).project
            except Task.DoesNotExist:
                return Project.objects.none()

    def has_object_action_permission(self, action, user, obj):
        return user in [
            getattr(obj.parent, 'owner', None),
            getattr(obj.parent, 'task_manager', None),
            getattr(obj.parent, 'promoter', None)
        ]

    def has_action_permission(self, action, user, model_cls, parent=None):
        """ Read permissions are allowed to any request, so we'll< always allow
        GET, HEAD or OPTIONS requests.
        """
        if action != 'POST':
            return True

        return user in [
            getattr(parent, 'owner', None),
            getattr(parent, 'task_manager', None),
            getattr(parent, 'promoter', None)
        ]


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
