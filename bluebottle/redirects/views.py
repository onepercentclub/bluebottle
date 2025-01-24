
from bluebottle.utils.views import ListAPIView, JsonApiViewMixin

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.redirects.models import Redirect
from bluebottle.redirects.serializers import RedirectSerializer


class RedirectPagination(BluebottlePagination):
    page_size = 2000


class RedirectListView(JsonApiViewMixin, ListAPIView):
    permission_classes = []

    queryset = Redirect.objects.all()
    serializer_class = RedirectSerializer
    pagination_class = RedirectPagination
