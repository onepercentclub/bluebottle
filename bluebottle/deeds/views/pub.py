from rest_framework.viewsets import ReadOnlyModelViewSet

from bluebottle.deeds.models import Deed
from bluebottle.deeds.serializers import DeedJSONLDSerializer


class DeedViewSet(ReadOnlyModelViewSet):
    """ViewSet for Deed model with JSON-LD serialization"""
    queryset = Deed.objects.all()
    serializer_class = DeedJSONLDSerializer
