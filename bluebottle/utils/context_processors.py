from django.conf import settings


def installed_apps_context_processor(request):
    bb_apps = []
    for app in settings.INSTALLED_APPS:
        if app[:11] == 'bluebottle.':
            # Ignore some standard apps
            if app[11:] not in ['common', 'admin_dashboard', 'contentplugins']:
                bb_apps.append(app[11:])
    context = {
        'installed_apps': settings.INSTALLED_APPS,
        'bb_apps': bb_apps,
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