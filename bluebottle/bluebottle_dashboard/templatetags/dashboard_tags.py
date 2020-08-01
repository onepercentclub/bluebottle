from bluebottle.members.models import MemberPlatformSettings
from django import template

from jet.utils import get_menu_items


register = template.Library()


@register.assignment_tag(takes_context=True)
def dashboard_get_menu(context):
    """
    Iterate over menu items and remove some based on feature flags
    """
    groups = get_menu_items(context)
    i = 0
    for group in groups:
        j = 0
        for item in group['items']:
            if item.get('name', '') == 'segmenttype':
                if not MemberPlatformSettings.load().enable_segments:
                    del groups[i]['items'][j]
            j += 1
        i += 1
    return groups
