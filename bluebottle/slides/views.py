from django.db.models import Q
from django.utils.timezone import now
from rest_framework import generics, permissions

from .models import Slide
from .serializers import SlideSerializer


# API views

class SlideList(generics.ListAPIView):
    model = Slide
    serializer_class = SlideSerializer
    permissions_classes = (permissions.SAFE_METHODS,)
    paginate_by = 10
    filter_fields = ('language', )

    def get_queryset(self):
        qs = super(SlideList, self).get_queryset()
        qs = qs.filter(status=Slide.SlideStatus.published)
        qs = qs.filter(publication_date__lte=now)
        qs = qs.filter(Q(publication_end_date__gte=now) | Q(publication_end_date__isnull=True))
        return qs
