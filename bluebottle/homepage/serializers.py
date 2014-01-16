from bluebottle.slides.serializers import SlideSerializer
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.quotes.serializers import QuoteSerializer

from rest_framework import serializers


class HomePageSerializer(serializers.Serializer):
    quotes = QuoteSerializer(source='quotes')
    slides = SlideSerializer(source='slides')
    projects = ProjectPreviewSerializer(source='projects')
