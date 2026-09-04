from collections import OrderedDict

from django.db.models import Model
from rest_framework_json_api.relations import HyperlinkedRelatedField


def _get_owners(instance):
    owners = getattr(instance, 'owners', None)
    if owners is None and hasattr(instance, 'activity'):
        owners = getattr(instance.activity, 'owners', None)
    return owners


def can_view_interests(request, instance):
    if not request or not getattr(request.user, 'is_authenticated', False):
        return False

    user = request.user
    if user.is_staff or user.is_superuser:
        return True

    owners = _get_owners(instance)
    if owners is None:
        return False

    return user in owners


def request_from_fields(fields):
    field = fields.get('interests') if hasattr(fields, 'get') else None
    if field is None:
        serializer = getattr(fields, 'serializer', None)
        if serializer is not None:
            field = serializer.fields.get('interests')
    if field is None:
        return None

    parent = getattr(field, 'parent', None)
    if parent is not None:
        return parent.context.get('request')
    return getattr(field, 'context', {}).get('request')


def omit_interests_if_unauthorized(fields, instance):
    """
    Return a copy of fields without interests when the current user must not
    see interested-people counts or lists.

    List serializers bind fields once without an instance, so popping in
    __init__ cannot hide this per object. The JSON:API renderer must filter
    here for list and included resources.
    """
    if not hasattr(fields, 'get') or 'interests' not in fields:
        return fields
    if can_view_interests(request_from_fields(fields), instance):
        return fields

    return OrderedDict(
        (key, value) for key, value in fields.items() if key != 'interests'
    )


def remove_interests_field_for_non_managers(serializer, instance):
    """
    Drop the interests field for unauthorized users.

    The JSON:API renderer builds relationship links via get_links(), so the
    field must be removed from the serializer to hide it completely.
    """
    if not isinstance(instance, Model) or 'interests' not in serializer.fields:
        return

    request = serializer.context.get('request')
    if not can_view_interests(request, instance):
        serializer.fields.pop('interests')


class InterestLinkField(HyperlinkedRelatedField):
    """
    Expose a counted interests link to activity owners and managers only.
    """

    def __init__(self, activity_level_only=True, slot_level=False, **kwargs):
        self.activity_level_only = activity_level_only
        self.slot_level = slot_level
        super().__init__(**kwargs)

    def get_interests_queryset(self, obj):
        return getattr(
            obj, self.source or self.field_name or self.parent.field_name
        )

    def get_count(self, queryset):
        if self.slot_level:
            return queryset.count()
        if self.activity_level_only:
            return queryset.filter(slot__isnull=True).count()
        return queryset.count()

    def get_links(self, obj=None, lookup_field="pk"):
        request = self.context.get('request')
        if obj is None or not can_view_interests(request, obj):
            return {}

        return_data = super().get_links(obj, lookup_field)
        url = self.reverse(
            self.related_link_view_name, args=(getattr(obj, lookup_field),)
        )
        return_data['related'] = {
            'href': url,
            'meta': {'count': self.get_count(self.get_interests_queryset(obj))},
        }
        return return_data
