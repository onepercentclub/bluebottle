from urllib.parse import urlparse

from django.db import connection
from django.urls import resolve, Resolver404
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


def iri_from_data(data):
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get('id') or data.get('iri')
    return None


def type_slug_from_iri(iri):
    if not iri:
        return None
    parts = [part for part in urlparse(iri).path.strip('/').split('/') if part]
    if 'json-ld' in parts:
        index = parts.index('json-ld')
        if len(parts) > index + 1:
            return parts[index + 1]
    return None


def type_from_iri(iri):
    if not iri:
        return None
    type_slug = None
    try:
        type_slug = resolve(urlparse(iri).path).kwargs['type']
    except (Resolver404, KeyError, TypeError, ValueError):
        type_slug = type_slug_from_iri(iri)
    if type_slug:
        return inflection.camelize(type_slug.replace('-', '_'), False)
    return None


def resource_type_from_iri(iri, allowed_types=None):
    from bluebottle.activity_pub.models import ActivityPubModel

    instance = ActivityPubModel.objects.from_iri(iri)
    if instance:
        try:
            type_name = instance.get_real_instance().__class__.__name__
            if not allowed_types or type_name in allowed_types:
                return type_name
        except Exception:
            pass

    resource_type = type_from_iri(iri)
    if resource_type == 'Actor' and allowed_types:
        if 'Organization' in allowed_types:
            return 'Organization'
        if 'Person' in allowed_types:
            return 'Person'

    if resource_type and (not allowed_types or resource_type in allowed_types):
        return resource_type
    if allowed_types:
        return allowed_types[0]
    return resource_type


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
