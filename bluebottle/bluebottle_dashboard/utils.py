from django.urls import reverse

from bluebottle.looker.models import LookerEmbed
from django import template
from django.apps import apps
from django.conf import settings
from jet.utils import get_menu_items as jet_get_menu_items

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
    i = 0
    for group in groups:
        j = 0
        properties = get_jet_item(group['label'])
        if 'enabled' in properties and properties['enabled']:
            prop = get_feature_flag(properties['enabled'])
            if not prop:
                del groups[i]
                i += 1
                continue
        for item in group['items']:
            name = item.get('name', None) or item.get('url', None)
            properties = get_jet_item(group['label'], name)
            if properties and 'enabled' in properties and properties['enabled']:
                prop = get_feature_flag(properties['enabled'])
                if not prop:
                    del groups[i]['items'][j]
            j += 1
        if group['app_label'] == 'looker':
            group['items'] = [{
                'url': reverse('jet-dashboard:looker-embed', args=(look.id,)),
                'url_blank': False,
                'name': 'lookerembed',
                'object_name': 'LookerEmbed',
                'label': look.title,
                'has_perms': True,
                'current': False} for look in LookerEmbed.objects.all()
            ]
        i += 1
    return groups
