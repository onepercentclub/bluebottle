import re

from django.conf import settings


def installed_apps_context_processor(request):
    context = {
        'installed_apps': settings.INSTALLED_APPS,
        'bb_apps': settings.BB_APPS,
    }
    return context


def google_analytics_code(request):
    """
    Add Google Analytics code from settings file to general request context.
    """
    try:
        context = {'ANALYTICS_CODE': settings.ANALYTICS_CODE}
    except AttributeError:
        context ={}
    return context


def google_maps_api_key(request):
    """
    Add Google Maps API key from settings file to general request context.
    """
    try:
        context = {'MAPS_API_KEY': settings.MAPS_API_KEY}
    except AttributeError:
        context = {}
    return context


def git_commit(request):
    """
    Make the git commit hash available in the templates.
    """
    try:
        context = {'GIT_COMMIT': settings.GIT_COMMIT}
    except AttributeError:
        context = {}
    return context


def sentry_dsn(request):
    """
    Make the Sentry / Raven DSN available in the templates *without* the secret key.
    """
    try:
        raven_config = settings.RAVEN_CONFIG['dsn']
    except AttributeError, KeyError:
        return {}

    match = re.search( r"https:\/\/([a-z|0-9]+):([a-z|0-9]+)\@app.getsentry.com\/(\d+)", raven_config, re.M|re.I)

    if not match:
        return {}
    else:
        public_key = match.group(1)
        project_id = match.group(3)

        return {'RAVEN_DSN': "https://{0}@app.getsentry.com/{1}".format(public_key, project_id)}


def conf_settings(request):
    """
    Some settings we want to make available in templates.
    """
    context = {}
    context['DEBUG'] = getattr(settings, 'DEBUG', False)
    context['COMPRESS_TEMPLATES'] = getattr(settings, 'COMPRESS_TEMPLATES', False)

    return context


def facebook_auth_settings(request):
    """
    Facebook Auth client side ID.
    """
    context = {}
    context['FACEBOOK_AUTH_ID'] = getattr(settings, 'SOCIAL_AUTH_FACEBOOK_KEY', '')

    return context


def mixpanel_settings(request):
    """
    Add Mixpanel API key from settings file to general request context.
    """
    try:
        context = {'MIXPANEL': settings.MIXPANEL}
    except AttributeError:
        context = {}
    return context;
