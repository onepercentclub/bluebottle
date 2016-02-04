from rest_framework import serializers


class SettingsSerializer(serializers.Serializer):
    """ Serializer for the Follow model """

    settings = serializers.CharField()
    id = serializers.CharField()

    class Meta:
        fields = ['id', 'settings']