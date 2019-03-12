import requests
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from requests import HTTPError
from social.exceptions import (AuthAlreadyAssociated, AuthCanceled,
                               AuthMissingParameter, AuthException)
from social_django.utils import psa, get_strategy, STORAGE


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
            social_auth = request.user.social_auth.get(provider=backend)

            if not self._check(social_auth, backend):
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({}, status=status.HTTP_201_CREATED)
        except (AuthCanceled, AuthMissingParameter, AuthException, HTTPError), e:
            return Response(
                {'error': 'Authentication process canceled: {}'.format(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AuthAlreadyAssociated:
            return Response(
                {'error': 'Another user for this facebook account already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _check(self, social_auth, backend):
        access_token = social_auth.access_token

        response = requests.get(
            'https://graph.facebook.com/me/permissions',
            headers={'Authorization': 'Bearer {}'.format(access_token)}
        )

        try:
            for perm in json.loads(response.content)['data']:
                if perm['permission'] == 'publish_actions' and perm['status'] == 'granted':
                    return True
        except KeyError:
            pass

        return False

    def get(self, request, backend):
        try:
            social_auth = request.user.social_auth.get(provider=backend)
            if self._check(social_auth, backend):
                return Response({}, status=status.HTTP_201_CREATED)
        except request.user.social_auth.model.DoesNotExist:
            pass

        return Response(
            {'error': 'No valid accesstoken found'},
            status=status.HTTP_404_NOT_FOUND
        )
