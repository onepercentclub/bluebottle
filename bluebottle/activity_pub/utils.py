from urllib.parse import urlparse

import inflection

from bluebottle.activity_pub.models import Organization as Organization
from bluebottle.clients import properties
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
    return urlparse(url).hostname == properties.tenant.domain_url


def get_platform_actor():
    site_settings = SitePlatformSettings.load()
    try:
        if site_settings.organization:
            platform_organization = site_settings.organization
            return platform_organization.activity_pub_organization
    except Organization.DoesNotExist:
        pass


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
