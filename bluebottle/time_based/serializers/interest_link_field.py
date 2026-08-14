from rest_framework_json_api.relations import HyperlinkedRelatedField


class InterestLinkField(HyperlinkedRelatedField):
    """
    Expose a counted interests link to activity owners and managers only.
    """

    def __init__(self, activity_level_only=True, slot_level=False, **kwargs):
        self.activity_level_only = activity_level_only
        self.slot_level = slot_level
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if not (
            request.user in instance.owners or
            request.user.is_staff or
            request.user.is_superuser
        ):
            return None
        return getattr(instance, self.source or 'interests')

    def get_count(self, instance):
        queryset = getattr(instance, self.source or 'interests')
        if self.slot_level:
            return queryset.count()
        if self.activity_level_only:
            return queryset.filter(slot__isnull=True).count()
        return queryset.count()

    def get_links(self, obj=None, lookup_field="pk"):
        links = super().get_links(obj, lookup_field)
        return {
            'related': {
                'href': links['related'],
                'meta': {'count': self.get_count(obj)},
            }
        }
