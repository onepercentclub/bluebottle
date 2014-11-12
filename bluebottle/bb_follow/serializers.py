from rest_framework import serializers
from bluebottle.bb_follow.models import Follow
from bluebottle.utils.model_dispatcher import get_project_model




class FollowedObjectRelatedField(serializers.RelatedField):
	""" A custom field for the followed_object field in the Follow model """

	def to_native(self, value):
		""" Serialize followed objects to a simple representation """

		if isinstance(value, get_project_model()):
			print "This is a project"


class FollowSerializer(serializers.ModelSerializer):
	followed_object = FollowedObjectRelatedField()

	class Meta:
		model = Follow
		fields = ('user', 'content_type', 'object_id', 'followed_object')

