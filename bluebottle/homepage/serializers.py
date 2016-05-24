from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.quotes.serializers import QuoteSerializer
from bluebottle.slides.serializers import SlideSerializer
from bluebottle.statistics.serializers import StatisticSerializer
from rest_framework import serializers


class HomePageSerializer(serializers.Serializer):
    id = serializers.CharField()
    quotes = QuoteSerializer(many=True)
    slides = SlideSerializer(many=True)
    statistics = StatisticSerializer(many=True)
    projects = ProjectPreviewSerializer(many=True)
