from django.db.models import Model
from rest_framework_json_api.relations import HyperlinkedRelatedField


def _get_owners(instance):
    owners = getattr(instance, 'owners', None)
    if owners is None and hasattr(instance, 'activity'):
        owners = getattr(instance.activity, 'owners', None)
    return owners


def can_view_interests(request, instance):
    if not request or not request.user.is_authenticated:
        return False

    owners = _get_owners(instance)
    if not owners:
        return False

    return (
        request.user in owners or
        request.user.is_staff or
        request.user.is_superuser
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
        return_data = super().get_links(obj, lookup_field)
        url = self.reverse(
            self.related_link_view_name, args=(getattr(obj, lookup_field),)
        )
        return_data['related'] = {
            'href': url,
            'meta': {'count': self.get_count(self.get_interests_queryset(obj))},
        }
        return return_data
