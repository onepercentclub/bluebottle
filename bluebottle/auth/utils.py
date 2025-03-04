from requests import request, HTTPError


from django.shortcuts import redirect

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from two_factor.admin import AdminSiteOTPRequired as BaseAdminSiteOTPRequired

from bluebottle.utils.models import get_languages


USER_MODEL = get_user_model()


def user_from_request(strategy, backend, *args, **kwargs):
    user = strategy.request.user

    if user.is_authenticated:
        return {'user': strategy.request.user}


def fallback_email(strategy, backend, *args, **kwargs):
    if 'email' not in kwargs['details']:
        kwargs['details']['email'] = kwargs['uid']


def save_profile_picture(strategy, user, response, details, backend,
                         is_new=False, *args, **kwargs):
    if is_new and backend.name == 'facebook':
        url = 'http://graph.facebook.com/{0}/picture'.format(response['id'])

        try:
            response = request('GET', url, params={'type': 'large'})
            response.raise_for_status()
        except HTTPError:
            pass
        else:
            if not user.picture:
                user.picture.save('{0}_fb_social.jpg'.format(user.username),
                                  ContentFile(response.content))
                user.save()


def refresh(strategy, social, *args, **kwargs):
    """Refresh the facebook token, so that we get a long lived backend token."""
    kwargs['response'].update(
        kwargs['backend'].refresh_token(kwargs['response']['access_token'])
    )


def set_language(strategy, user, response, details,
                 is_new=False, *args, **kwargs):
    supported_languages = [lang.code for lang in get_languages()]

    try:
        language = response['locale'][:2]
        if language in supported_languages:
            user.primary_language = language
            user.save()
    except KeyError:
        pass


def get_extra_facebook_data(strategy, user, response, details,
                            is_new=False, *args, **kwargs):
    """
        From Facebook we get the following properties with the 'public_profile'
        permission:
        id, name, first_name, last_name, link, gender, locale, age_range
    """

    if not user.first_name:
        user.first_name = response.get('first_name', '')
    if not user.last_name:
        user.last_name = response.get('last_name', '')

    user.save()


class AdminSiteOTPRequired(BaseAdminSiteOTPRequired):
    def login(self, request, extra_context=None):

        if request.user.is_authenticated and not request.user.is_verified():
            next = request.GET.get('next')
            if next:
                request.session['next'] = next
            return redirect('two_factor:setup')

        return super().login(request, extra_context)
