from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from social.apps.django_app.utils import psa, get_strategy, STORAGE


def load_drf_strategy(request=None):
    return get_strategy('bluebottle.social.strategy.DRFStrategy', STORAGE, request)


@psa(redirect_uri='/en/', load_strategy=load_drf_strategy)
def store_token(request, backend):
    return request.backend.auth_complete()


class AccessTokenView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, backend):
        user = store_token(request, backend)
        return Response()




