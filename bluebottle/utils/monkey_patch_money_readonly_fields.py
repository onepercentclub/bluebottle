import django.contrib.admin.utils as admin_utils
import django.contrib.admin.helpers as admin_helpers
import django.contrib.admin.templatetags.admin_list as admin_list

from djmoney.models.fields import MoneyField

MODULES_TO_PATCH = [admin_utils, admin_helpers, admin_list]


original_display_for_field = admin_utils.display_for_field


def display_for_field(value, field, empty):
    if isinstance(field, MoneyField):
        return unicode(value)

    return original_display_for_field(value, field, empty)

# FIXME: Do not monkeypatch this when django-money is fixed
for mod in MODULES_TO_PATCH:
    setattr(mod, 'display_for_field', display_for_field)
