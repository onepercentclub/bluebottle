from builtins import object

from rest_framework import serializers

from bluebottle.tasks.models import Skill


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta(object):
        model = Skill
        fields = ('id', 'name', 'expertise')

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'skills'
