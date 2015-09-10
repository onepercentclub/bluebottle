from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from social.exceptions import AuthAlreadyAssociated
from social.apps.django_app.utils import psa, get_strategy, STORAGE


def load_drf_strategy(request=None):
    return get_strategy('bluebottle.social.strategy.DRFStrategy', STORAGE, request)


@psa(
    redirect_uri='/static/assets/frontend/popup.html', load_strategy=load_drf_strategy
)
def store_token(request, backend):
    return request.backend.auth_complete()


class AccessTokenView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, backend):
        try:
            store_token(request, backend)
            return Response({})
        except AuthAlreadyAssociated:
            return Response(
                {'error': 'Another user for this facebook account already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )
