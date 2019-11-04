from rest_framework import permissions


class ApplicantDocumentPermission(permissions.DjangoModelPermissions):

    def has_object_permission(self, request, view, obj):
        if not obj:
            return True
        if obj and request.user in [
            obj.user,
            obj.activity.owner,
            obj.activity.initiative.activity_manager
        ]:
            return True
        return False
