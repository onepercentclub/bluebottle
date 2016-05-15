from rest_framework import serializers
from bluebottle.bb_follow.models import Follow
from bluebottle.projects.models import Project


class FollowedObjectRelatedField(serializers.RelatedField):
    """ A custom field for the followed_object field in the Follow model """

    def to_native(self, value):
        """ Serialize followed objects to a simple representation """

        if isinstance(value, Project):
            # For now, simply return only slug of the project. Alternatively,
            # we could consider returning a nested objects
            return value.slug

        if value:
            return value.id


class FollowSerializer(serializers.ModelSerializer):
    """ Serializer for the Follow model """
    followed_object = FollowedObjectRelatedField()

    class Meta:
        model = Follow
        fields = ('user', 'content_type', 'object_id', 'followed_object')
