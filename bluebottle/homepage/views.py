from django.utils import translation

from rest_framework import response

from bluebottle.utils.views import GenericAPIView
from .models import HomePage
from .serializers import HomePageSerializer


# Instead of serving all the objects separately we combine Slide, Quote and Stats into a dummy object
class HomePageDetail(GenericAPIView):
    serializer_class = HomePageSerializer
    model_class = HomePage

    def get(self, request, language='en'):

        # Force requested language
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        homepage = HomePage().get(language)
        serialized = HomePageSerializer().to_representation(homepage)
        return response.Response(serialized)
