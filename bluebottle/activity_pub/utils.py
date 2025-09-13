import inflection
from urllib.parse import urlparse

from bluebottle.activity_pub.models import PubOrganization
from bluebottle.organizations.models import Organization

from bluebottle.cms.models import SitePlatformSettings

from bluebottle.clients import properties


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
        platform_organization = site_settings.organization
        return platform_organization.puborganization
    except (Organization.DoesNotExist, PubOrganization.DoesNotExist):
        return None
