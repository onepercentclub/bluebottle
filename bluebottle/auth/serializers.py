from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_json_api.serializers import Serializer
from social_core.exceptions import AuthCanceled
from social_core.utils import get_strategy
from social_django.utils import psa, STORAGE


def load_drf_strategy(request=None):
    return get_strategy('bluebottle.social.strategy.DRFStrategy', STORAGE, request)


@psa(redirect_uri='/static/assets/frontend/popup.html',
     load_strategy=load_drf_strategy)
def complete(request, backend):
    try:
        user = request.backend.auth_complete(request=request)
    except AuthCanceled:
        return None
    if not user.is_active:
        raise AuthenticationFailed('User account is de-activated')
    return user


class FacebookAuthSerializer(Serializer):
    access_token = serializers.CharField(write_only=True)
    signed_request = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = complete(request, 'facebook')

        return {'user': user}

    def create(self, data, *args, **kwargs):
        user = data['user']
        user.last_login = now()
        user.save()
        return type('obj', (object,), {
            'pk': user.id,
            'token': data['user'].get_jwt_token()
        })

    class Meta:
        fields = ['access_token', 'signed_request', 'token']

    class JSONAPIMeta:
        resource_name = 'auth/token'
