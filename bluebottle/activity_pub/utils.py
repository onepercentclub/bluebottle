from urllib.parse import urlparse

from django.db import connection
import inflection
from django.urls import Resolver404, resolve

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


def tenant_hostname():
    return connection.tenant.domain_url.split(':', 1)[0].lower()


def is_local(url):
    if not url:
        return False
    hostname = urlparse(url).hostname
    return bool(hostname) and hostname.lower() == tenant_hostname()


def normalize_resource_url(url):
    if not url:
        return url
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    hostname = parsed.hostname
    if not hostname:
        return url
    port = parsed.port
    if port is None and 'localhost' in hostname:
        port = 3000
    netloc = f'{hostname}:{port}' if port else hostname
    return f'{parsed.scheme}://{netloc}{path}'


def urls_equivalent(url_a, url_b):
    if not url_a or not url_b:
        return False
    return normalize_resource_url(url_a) == normalize_resource_url(url_b)


def resource_type_from_url(url, allowed_types):
    path_parts = [part for part in urlparse(url).path.split('/') if part]
    if len(path_parts) < 2:
        return None

    path_segment = path_parts[-2]
    for resource_type in allowed_types:
        if inflection.dasherize(inflection.underscore(resource_type)) == path_segment:
            return resource_type
    return None


def resolve_local_resource(iri):
    from bluebottle.activity_pub.models import ActivityPubModel

    if not is_local(iri):
        return None

    try:
        resolved = resolve(urlparse(iri).path)
        instance = ActivityPubModel.objects.filter(pk=resolved.kwargs['pk']).first()
        if instance:
            return instance
    except Resolver404:
        pass

    platform_actor = get_platform_actor()
    if platform_actor and urls_equivalent(iri, platform_actor.pub_url):
        return platform_actor

    return None


def get_local_resource_data(url):
    from bluebottle.clients.models import Client
    from bluebottle.clients.utils import LocalTenant
    from bluebottle.activity_pub.models import ActivityPubModel
    from bluebottle.activity_pub.serializers import ActivityPubSerializer

    hostname = urlparse(url).hostname
    if not hostname:
        return None

    tenant = Client.objects.filter(domain_url__iexact=hostname).first()
    if not tenant:
        return None

    with LocalTenant(tenant):
        instance = resolve_local_resource(url)
        if not instance:
            instance = ActivityPubModel.objects.from_iri(url)
        if instance:
            return ActivityPubSerializer(instance=instance).data

    return None


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
