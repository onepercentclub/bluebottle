#from social_auth.decorators import
from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from rest_framework import parsers, renderers, status
from rest_framework.authentication import get_authorization_header
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from social.apps.django_app.utils import strategy


class GetAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    model = Token

    # Accept backend as a parameter and 'auth' for a login / pass
    def post(self, request, backend):
        serializer = self.serializer_class(data=request.DATA)

        # Here we call PSA to authenticate like we would if we used PSA on server side.
        token_result = register_by_access_token(request, backend)

        # If user is active we get or create the REST token and send it back with user data
        if token_result.get('token', None):
            return Response({'token': token_result.get('token')})
        elif token_result.get('error', None):
            return Response({'error': token_result.get('error')})
        return Response({'error': _('No result for token')})

@strategy()
def register_by_access_token(request, backend):
    backend = request.strategy.backend

    access_token = request.DATA.get('accessToken', None)

    if access_token:
        user = backend.do_auth(access_token)
        if user and user.is_active:
            user.last_login = datetime.now()
            user.save()
            return {'token': user.get_jwt_token()}
        elif user and not user.is_active:
            return {'error': _("This user account is disabled, please contact us if you want to re-activate.")}
        else:
            return None
    return None
