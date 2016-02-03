from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.quotes.serializers import QuoteSerializer
from bluebottle.slides.serializers import SlideSerializer
from bluebottle.statistics.serializers import StatisticSerializer
from rest_framework import serializers


class HomePageSerializer(serializers.Serializer):
    id = serializers.CharField(source='id')
    quotes = QuoteSerializer(source='quotes', many=True)
    slides = SlideSerializer(source='slides', many=True)
    statistics = StatisticSerializer(source='statistics', many=True)
    projects = ProjectPreviewSerializer(source='projects', many=True)
