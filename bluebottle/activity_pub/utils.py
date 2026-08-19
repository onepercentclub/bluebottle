from urllib.parse import urlparse

from django.db import connection
import inflection

from bluebottle.cms.models import SitePlatformSettings


def transform(data, func, *args, **kwargs):
    if not isinstance(data, dict):
        return data

    if isinstance(data, dict):
        return dict(
            (func(key, *args, **kwargs), transform(value, func, *args, **kwargs))
            for key, value in data.items()
        )
    elif isinstance(data, (tuple, list)):
        return type(data)(transform(item, func, *args, **kwargs) for item in data)
    else:
        return data


def underscore(data):
    return transform(data, inflection.underscore)


def camelize(data, initial=True):
    return transform(data, inflection.camelize, initial)


def is_local(url):
    return urlparse(url).hostname == connection.tenant.domain_url


def get_platform_actor():
    site_settings = SitePlatformSettings.load()
    if site_settings.organization and hasattr(site_settings.organization, 'activity_pub_model'):
        return site_settings.organization.activity_pub_model


def timedelta_to_iso(td):
    sign = '-' if td.total_seconds() < 0 else ''
    td = -td if td.total_seconds() < 0 else td

    days = td.days
    seconds = td.seconds
    micros = td.microseconds

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = ['P']
    if days:
        parts.append(f'{days}D')

    time_parts = []
    if hours:
        time_parts.append(f'{hours}H')
    if minutes:
        time_parts.append(f'{minutes}M')

    if seconds or micros:
        total_sec = seconds + micros / 1_000_000
        s = f'{total_sec:.6f}'.rstrip('0').rstrip('.')
        time_parts.append(f'{s}S')

    if not days and not time_parts:
        return 'PT0S'

    if time_parts:
        parts.append('T')
        parts.extend(time_parts)

    return sign + ''.join(parts)


def resource_iri(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get('id') or value.get('iri')
    return None


def event_for_team(team):
    from bluebottle.activity_pub.models import Team as ActivityPubTeam

    ap_team = getattr(team, 'origin', None)
    if isinstance(ap_team, ActivityPubTeam) and ap_team.attributed_to_id:
        return ap_team.attributed_to
    activity = getattr(team, 'activity', None)
    return getattr(activity, 'activity_pub_model', None)


def platform_may_modify_event(platform, event):
    from bluebottle.activity_pub.models import Create, Follow

    if platform is None or event is None:
        return False
    if Create.objects.filter(object=event, recipients__actor=platform).exists():
        return True
    for create in event.create_set.all():
        if Follow.objects.filter(actor=platform, object=create.actor).exists():
            return True
    return False


def sending_platform(request=None, activity_iri=None):
    if request is not None and getattr(request, 'auth', None):
        return request.auth

    from bluebottle.activity_pub.models import ActivityPubModel

    activity = ActivityPubModel.objects.from_iri(activity_iri) if activity_iri else None
    return getattr(activity, 'platform', None)
