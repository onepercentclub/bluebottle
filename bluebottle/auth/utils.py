import time
from datetime import datetime
from requests import request, HTTPError

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from bluebottle.bb_accounts.utils import valid_email, send_welcome_mail
from bluebottle.clients import properties

USER_MODEL = get_user_model()


def user_from_request(strategy, backend, *args, **kwargs):
    user = strategy.request.user

    if user.is_authenticated():
        return {'user': strategy.request.user}


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
    social.refresh_token(strategy)


def set_language(strategy, user, response, details,
                 is_new=False, *args, **kwargs):
    supported_langauges = [
        lang_code for (lang_code, lang_name) in getattr(properties,
                                                        'LANGUAGES')]

    try:
        language = response['locale'][:2]
        if language in supported_langauges:
            user.primary_language = language
        else:
            user.primary_language = properties.LANGUAGE_CODE

        user.save()
    except KeyError:
        user.primary_language = properties.LANGUAGE_CODE


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
    if not user.gender:
        user.gender = response.get('gender', '')

    fb_link = response.get('link', None)

    birthday = response.get('birthday', None)
    if birthday and not user.birthdate:
        birthdate = time.strptime(birthday, "%m/%d/%Y")
        user.birthdate = datetime.fromtimestamp(time.mktime(birthdate))

    if fb_link and len(fb_link) < 50:
        user.facebook = fb_link

    user.save()


def send_welcome_mail_pipe(strategy, user, response, details,
                           is_new=False, *args, **kwargs):
    """
    The post_save signal handler in bb_accounts.models deals with sending a
    welcome mail. However, because the User object passes through the social
    pipeline it gets saved several time and therefore losing the "new" status
    to trigger sending an email. This pipe in the social pipeline therefore
    sends an explicit welcome email.
    """

    if is_new and valid_email(user.email):
        send_welcome_mail(user)
