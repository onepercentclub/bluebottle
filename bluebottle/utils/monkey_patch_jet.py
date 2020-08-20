from django.contrib.admin import ModelAdmin
from django.views.decorators.csrf import csrf_protect

import jet.dashboard.views


jet.dashboard.views.add_user_dashboard_module_view = csrf_protect(jet.dashboard.views.add_user_dashboard_module_view)
jet.dashboard.views.remove_dashboard_module_view = csrf_protect(jet.dashboard.views.remove_dashboard_module_view)
jet.dashboard.views.update_dashboard_modules_view = csrf_protect(jet.dashboard.views.update_dashboard_modules_view)


original_formfield_for_manytomany = ModelAdmin.formfield_for_manytomany


def formfield_for_manytomany(self, db_field, request, **kwargs):
    """
    Override formfield_for_manytomany so we don't print how to do multiselect,
    because we use the standard widget for that.
    """
    form_field = original_formfield_for_manytomany(self, db_field, request, **kwargs)
    form_field.help_text = db_field.help_text
    return form_field


ModelAdmin.formfield_for_manytomany = formfield_for_manytomany
