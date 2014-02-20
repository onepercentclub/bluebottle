from rest_framework import generics
from rest_framework import permissions
from .models import Slide
from .serializers import SlideSerializer
from django.utils.timezone import now
from django.db.models import Q

# API views

class SlideList(generics.ListAPIView):
    model = Slide
    serializer_class = SlideSerializer
    permissions_classes = (permissions.SAFE_METHODS,)
    paginate_by = 10

    def get_queryset(self):
        qs = super(SlideList, self).get_queryset()

        # Set language if supplied
        language = self.request.QUERY_PARAMS.get('language', None)
        if language:
            qs = qs.filter(language=language)

        qs = qs.filter(status=Slide.SlideStatus.published)
        qs = qs.filter(publication_date__lte=now)
        qs = qs.filter(Q(publication_end_date__gte=now) | Q(publication_end_date__isnull=True))
        return qs


