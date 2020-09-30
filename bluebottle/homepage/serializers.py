from rest_framework import serializers


class HomePageSerializer(serializers.Serializer):
    id = serializers.CharField()
