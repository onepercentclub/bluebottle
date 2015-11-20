from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.quotes.serializers import QuoteSerializer
from bluebottle.slides.serializers import SlideSerializer
from bluebottle.statistics.serializers import StatisticSerializer
from rest_framework import serializers


class HomePageSerializer(serializers.Serializer):
    id = serializers.CharField(source='id')
    quotes = QuoteSerializer(source='quotes')
    slides = SlideSerializer(source='slides')
    impact = StatisticSerializer(source='stats')
    projects = ProjectPreviewSerializer(source='projects')
