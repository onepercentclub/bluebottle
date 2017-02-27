from rest_framework import permissions


class IsFinancialMember(permissions.BasePermission):
    """
    Allows access only to financial members
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Financial').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='Financial').exists()
