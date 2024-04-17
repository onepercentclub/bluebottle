from django import template
from django.apps import apps
from django.conf import settings
from django.urls import reverse
from jet.utils import get_menu_items as jet_get_menu_items
from bluebottle.analytics.models import AnalyticsPlatformSettings

from bluebottle.looker.models import LookerEmbed
from bluebottle.segments.models import SegmentType

register = template.Library()


def get_jet_item(label, model=None):
    labels = settings.JET_SIDE_MENU_ITEMS
    for la in labels:
        if la['label'] == label or la.get('app_label', False) == label:
            if model:
                for it in la['items']:
                    name = it.get('name', None) or it.get('url', None)
                    if name.split('.')[1] == model:
                        return it
            else:
                return la


def get_feature_flag(flag_path):
    app, model, prop = flag_path.split('.')
    app_settings = apps.get_model(app, model).load()
    return getattr(app_settings, prop, False)


def get_menu_items(context):
    """
    Iterate over menu items and remove some based on feature flags
    """
    groups = jet_get_menu_items(context)
    for group in groups:
        properties = get_jet_item(group['label'])
        if 'enabled' in properties and properties['enabled']:
            prop = get_feature_flag(properties['enabled'])
            if not prop:
                group['hide'] = True
        for item in group['items']:
            name = item.get('name', None) or item.get('url', None)
            properties = get_jet_item(group['label'], name)
            if properties and 'enabled' in properties and properties['enabled']:
                prop = get_feature_flag(properties['enabled'])
                if not prop:
                    item["hide"] = True
        if group["app_label"] == "looker":
            (analytics_settings, _) = AnalyticsPlatformSettings.objects.get_or_create()

            group['items'] = [{
                'url': reverse('jet-dashboard:looker-embed', args=(look.id,)),
                'url_blank': False,
                'name': 'lookerembed',
                'object_name': 'LookerEmbed',
                'label': look.title,
                'has_perms': True,
                'current': False} for look in LookerEmbed.objects.all()
            ]

            if analytics_settings.plausible_embed_link:
                group["items"].append(
                    {
                        "url": reverse("jet-dashboard:plausible-embed"),
                        "url_blank": False,
                        "object_name": "LookerEmbed",
                        "name": "plausible",
                        "label": "Analytics",
                        "has_perms": True,
                        "current": False,
                    }
                )
        if group["app_label"] == "segments":
            group["items"] += [
                {
                    "url": reverse(
                        "admin:segments_segmenttype_change", args=(segment_type.id,)
                    ),
                    "url_blank": False,
                    "name": "segmenttype",
                    "object_name": "SegmentType",
                    "label": segment_type.name,
                    "has_perms": True,
                    "current": False,
                }
                for segment_type in SegmentType.objects.all()
            ]

    for group in list(groups):
        if 'hide' in group:
            groups.remove(group)
        else:
            for item in list(group['items']):
                if 'hide' in item:
                    group['items'].remove(item)
    return groups
