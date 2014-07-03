from requests import request, HTTPError
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from bluebottle.auth.exceptions import EmailExists

USER_MODEL = get_user_model()

def save_profile_picture(strategy, user, response, details,
                         is_new=False,*args,**kwargs):

    if is_new and strategy.backend.name == 'facebook':
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



def get_extra_facebook_data(strategy, user, response, details, is_new=False, *args, **kwargs):
    """ From Facebook we get the following properties with the 'public_profile' permission:
        id, name, first_name, last_name, link, gender, locale, age_range
    """

    user.first_name = response.get('first_name', None)
    user.last_name = response.get('last_name', None)
    user.gender = response.get('gender', None)
    fb_link = response.get('link', None)
    if len(fb_link) < 50:
        user.facebook = fb_link
    user.save()