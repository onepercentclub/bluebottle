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


def hostname_from_url(url):
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    return parsed.hostname.lower()


def get_tenant_for_url(url):
    from bluebottle.clients.models import Client

    hostname = hostname_from_url(url)
    if not hostname:
        return None
    domain = hostname.split(':', 1)[0]
    return Client.objects.filter(domain_url__iexact=domain).first()


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

    normalized_iri = normalize_resource_url(iri)
    for candidate in (iri, normalized_iri):
        if not candidate:
            continue
        instance = ActivityPubModel.objects.non_polymorphic().filter(iri=candidate).first()
        if instance:
            resolved = safe_get_real_instance(instance)
            if resolved:
                return resolved

    try:
        resolved = resolve(urlparse(iri).path)
        instance = ActivityPubModel.objects.non_polymorphic().filter(
            pk=resolved.kwargs['pk']
        ).first()
        if instance:
            real_instance = safe_get_real_instance(instance)
            if real_instance:
                return real_instance
    except Resolver404:
        pass

    platform_actor = get_platform_actor()
    if platform_actor and urls_equivalent(iri, platform_actor.pub_url):
        return platform_actor

    return None


def get_local_resource_data(url):
    from bluebottle.activity_pub.serializers import ActivityPubSerializer
    from bluebottle.clients.utils import LocalTenant

    tenant = get_tenant_for_url(url)
    if not tenant:
        return None

    with LocalTenant(tenant):
        instance = resolve_local_resource(url)
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


def get_create_for_object(obj):
    from bluebottle.activity_pub.models import Create

    if not obj.pk:
        return None

    return (
        Create.objects.non_polymorphic()
        .filter(object_id=obj.pk)
        .order_by('pk')
        .first()
    )


def get_follow_for_actor(actor):
    from bluebottle.activity_pub.models import Follow

    actor_id = actor.pk if hasattr(actor, 'pk') else actor
    if not actor_id:
        return None

    return (
        Follow.objects.non_polymorphic()
        .filter(object_id=actor_id)
        .order_by('pk')
        .first()
    )


def safe_get_real_instance(instance):
    from polymorphic.models import PolymorphicTypeInvalid

    if instance is None:
        return None

    try:
        return instance.get_real_instance()
    except PolymorphicTypeInvalid:
        return None


def find_activity_pub_instance(iri):
    from bluebottle.activity_pub.models import ActivityPubModel

    if not iri:
        return None

    instance = ActivityPubModel.objects.from_iri(iri)
    if instance:
        return instance

    for candidate in (iri, normalize_resource_url(iri)):
        if not candidate:
            continue
        row = ActivityPubModel.objects.non_polymorphic().filter(iri=candidate).first()
        if row:
            resolved = safe_get_real_instance(row)
            if resolved:
                return resolved

    if is_local(iri):
        return resolve_local_resource(iri)

    return None


def safe_get_real_instance_class(instance):
    from polymorphic.models import PolymorphicTypeInvalid

    if instance is None:
        return None

    try:
        return instance.get_real_instance_class()
    except PolymorphicTypeInvalid:
        return None


def activity_pub_type_name(instance):
    real_class = safe_get_real_instance_class(instance)
    if real_class:
        return real_class.__name__
    return '-'


def activity_pub_verbose_type(instance):
    real_class = safe_get_real_instance_class(instance)
    if real_class:
        return real_class._meta.verbose_name
    return '-'


def get_transitions_for_object(obj):
    from bluebottle.activity_pub.models import Transition

    if not obj.pk:
        return []

    transitions = []
    for transition in Transition.objects.non_polymorphic().filter(object_id=obj.pk):
        real_instance = safe_get_real_instance(transition)
        if real_instance:
            transitions.append(real_instance)
    return transitions


def resolve_activity_pub_image_url(image_iri, payload=None):
    from bluebottle.activity_pub.clients import client
    from bluebottle.activity_pub.models import Image as ActivityPubImage

    if not image_iri:
        return None

    image = ActivityPubImage.objects.from_iri(image_iri)
    image_url = image.url if image else None

    if not image_url and payload:
        image_url = payload.get('url')

    if not image_url:
        local_data = get_local_resource_data(image_iri)
        if isinstance(local_data, dict):
            image_url = local_data.get('url')

    if not image_url and not is_local(image_iri):
        fetched = client.fetch(image_iri)
        if isinstance(fetched, dict):
            image_url = fetched.get('url')

    return image_url


def link_activity_pub_adopted(origin_iri, adopted):
    from bluebottle.activity_pub.models import ActivityPubModel, Image as ActivityPubImage

    if not origin_iri or not adopted:
        return

    origin = ActivityPubModel.objects.from_iri(origin_iri)
    if not origin or not hasattr(origin, 'adopted'):
        return

    adopted_pk = getattr(adopted, 'pk', None)
    if not adopted_pk:
        return

    if getattr(origin, 'adopted_id', None) == adopted_pk:
        return

    if isinstance(origin, ActivityPubImage):
        if ActivityPubImage.objects.filter(adopted_id=adopted_pk).exists():
            return

    origin.adopted = adopted
    origin.save(update_fields=['adopted'])
