import jet.dashboard.views
import jet.utils
from django.contrib.admin import ModelAdmin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from bluebottle.bluebottle_dashboard.utils import get_menu_items

jet.dashboard.views.add_user_dashboard_module_view = csrf_protect(
    jet.dashboard.views.add_user_dashboard_module_view)
jet.dashboard.views.remove_dashboard_module_view = csrf_protect(
    jet.dashboard.views.remove_dashboard_module_view)
jet.dashboard.views.update_dashboard_modules_view = csrf_protect(
    jet.dashboard.views.update_dashboard_modules_view)
jet.dashboard.views.update_dashboard_module_collapse_view = csrf_protect(
    jet.dashboard.views.update_dashboard_module_collapse_view)
jet.dashboard.views.load_dashboard_module_view = csrf_protect(
    jet.dashboard.views.load_dashboard_module_view)
jet.dashboard.views.reset_dashboard_view = csrf_protect(
    jet.dashboard.views.reset_dashboard_view)


original_dispatch = jet.dashboard.views.UpdateDashboardModuleView.dispatch


@method_decorator(csrf_protect)
def patched_dispatch(self, request, *args, **kwargs):
    return original_dispatch(self, request, *args, **kwargs)


jet.dashboard.views.UpdateDashboardModuleView.dispatch = patched_dispatch


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

jet.utils.get_menu_items = get_menu_items



_original_get_model_queryset = jet.utils.get_model_queryset


def get_model_queryset(admin_site, model, request, preserved_filters=None):
    """
    Jet prev/next builds a ChangeList including list_filter choice labels.

    RelatedFieldListFilter / SortedRelatedFieldListFilter then load every related
    object (and parler translations) on every change page. Filters are not needed
    to resolve sibling objects, so skip them.
    """
    model_admin = admin_site._registry.get(model)
    if model_admin is None:
        return

    original_get_list_filter = model_admin.get_list_filter
    model_admin.get_list_filter = lambda request: []
    try:
        return _original_get_model_queryset(
            admin_site, model, request, preserved_filters=preserved_filters
        )
    finally:
        model_admin.get_list_filter = original_get_list_filter


jet.utils.get_model_queryset = get_model_queryset

# Change this to bust the cached JS/CSS builds
jet.VERSION = jet.VERSION + 'goodup-1'
