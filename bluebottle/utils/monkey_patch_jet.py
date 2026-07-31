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


from django.contrib.admin.options import IncorrectLookupParameters
from django.urls import NoReverseMatch, reverse


def get_model_queryset(admin_site, model, request, preserved_filters=None):
    """
    Jet prev/next builds a ChangeList to find sibling objects.

    The stock implementation passes model_admin.get_list_filter(), and
    RelatedFieldListFilter / SortedRelatedFieldListFilter then load every
    related object (plus parler translations) on every change page.

    Filters are not applied from the change-page request anyway (Jet builds
    a changelist URL with preserved filters but never uses it), so construct
    the ChangeList with an empty list_filter. No shared ModelAdmin mutation.
    """
    model_admin = admin_site._registry.get(model)
    if model_admin is None:
        return

    try:
        reverse(
            '%s:%s_%s_changelist' % (
                admin_site.name,
                model._meta.app_label,
                model._meta.model_name,
            )
        )
    except NoReverseMatch:
        return

    list_display = model_admin.get_list_display(request)
    list_display_links = model_admin.get_list_display_links(request, list_display)
    search_fields = (
        model_admin.get_search_fields(request)
        if hasattr(model_admin, 'get_search_fields')
        else model_admin.search_fields
    )
    list_select_related = (
        model_admin.get_list_select_related(request)
        if hasattr(model_admin, 'get_list_select_related')
        else model_admin.list_select_related
    )

    actions = model_admin.get_actions(request)
    if actions:
        list_display = ['action_checkbox'] + list(list_display)

    ChangeList = model_admin.get_changelist(request)
    change_list_args = [
        request,
        model,
        list_display,
        list_display_links,
        [],  # skip list_filter choice enumeration
        model_admin.date_hierarchy,
        search_fields,
        list_select_related,
        model_admin.list_per_page,
        model_admin.list_max_show_all,
        model_admin.list_editable,
        model_admin,
    ]

    try:
        change_list_args.append(model_admin.get_sortable_by(request))
    except AttributeError:
        pass

    try:
        change_list_args.append(
            model_admin.get_search_help_text(request)
            if hasattr(model_admin, 'get_search_help_text')
            else model_admin.search_help_text
        )
    except AttributeError:
        pass

    try:
        return ChangeList(*change_list_args).get_queryset(request)
    except IncorrectLookupParameters:
        return model_admin.get_queryset(request)


jet.utils.get_model_queryset = get_model_queryset

# Change this to bust the cached JS/CSS builds
jet.VERSION = jet.VERSION + 'goodup-1'
