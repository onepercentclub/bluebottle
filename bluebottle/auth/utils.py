from django.utils.timezone import now

from django.shortcuts import redirect

from django.contrib.auth import get_user_model

from two_factor.admin import AdminSiteOTPRequired as BaseAdminSiteOTPRequired

from bluebottle.utils.models import get_languages


USER_MODEL = get_user_model()


def user_from_request(strategy, *args, **kwargs):
    user = strategy.request.user

    if user.is_authenticated:
        return {'user': strategy.request.user}


def set_language(user, response, *args, **kwargs):
    supported_languages = [lang.code for lang in get_languages()]

    try:
        language = response['locale'][:2]
        if language in supported_languages:
            user.primary_language = language
            user.save()
    except KeyError:
        pass


def set_last_login(user, response, *args, **kwargs):
    user.last = now()
    user.save()


class AdminSiteOTPRequired(BaseAdminSiteOTPRequired):
    def login(self, request, extra_context=None):

        if request.user.is_authenticated and not request.user.is_verified():
            next = request.GET.get('next')
            if next:
                request.session['next'] = next
            return redirect('two_factor:setup')

        return super().login(request, extra_context)
