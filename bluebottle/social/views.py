import requests

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

    def _check(self, social_auth, backend):
        extra_data = social_auth.extra_data
        access_token = extra_data['access_token']
        requested_scopes = extra_data.get('requested_scope', [])

        response = requests.get(
            'https://graph.facebook.com/me',
            headers={'Authorization': 'Bearer {}'.format(access_token)}
        )
        return response.status_code == 200 and 'publish_actions' in requested_scopes

    def get(self, request, backend):
        social_auth = request.user.social_auth.get(provider=backend)

        if social_auth:
            if self._check(social_auth, backend):
                return Response({})

        return Response(
            {'error': 'No access valid token found'},
            status=status.HTTP_404_NOT_FOUND
        )
