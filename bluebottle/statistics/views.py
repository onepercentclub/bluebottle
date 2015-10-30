from rest_framework import generics
from .serializers import StatisticSerializer
from .statistics import Statistics


# API views
class StatisticDetail(generics.RetrieveAPIView):
    serializer_class = StatisticSerializer

    def get_object(self, queryset=None):
        return Statistics()
