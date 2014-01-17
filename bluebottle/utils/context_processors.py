from django.conf import settings


def installed_apps_context_processor(request):
    bb_apps = []
    for app in settings.INSTALLED_APPS:
        if app[:11] == 'bluebottle.':
            # Ignore some standard apps
            if app[11:] not in ['common', 'admin_dashboard']:
                bb_apps.append(app[11:])
    context = {
        'installed_apps': settings.INSTALLED_APPS,
        'bb_apps': bb_apps,
    }
    return context
