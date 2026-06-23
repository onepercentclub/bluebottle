from builtins import str

from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin, SortableTabularInline
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from fluent_contents.admin.contentitems import BaseContentItemInline
import nested_admin

from bluebottle.cms.fluent_admin import NestedContentItemFormSet, get_cms_content_item_inlines
from parler.admin import TranslatableAdmin
from solo.admin import SingletonModelAdmin

from bluebottle.cms.models import (
    SiteLinks, Link, LinkGroup, LinkPermission, SitePlatformSettings,
    Stat, Quote, Person, Step, Logo, ResultPage, HomePage, ContentLink,
    Greeting
)
from bluebottle.members.models import Member
from bluebottle.statistics.statistics import Statistics
from bluebottle.translations.admin import TranslatableLabelAdminMixin
from bluebottle.utils.admin import BasePlatformSettingsAdmin
from bluebottle.utils.widgets import SecureAdminURLFieldWidget


@admin.register(LinkPermission)
class LinkPermissionAdmin(admin.ModelAdmin):
    model = LinkPermission

    def get_model_perms(self, request):
        return {}


class LinkInline(SortableStackedInline):
    model = Link
    extra = 0

    fields = (
        'title', 'groups',
        'highlight', 'open_in_new_tab',
        'link'
    )


@admin.register(LinkGroup)
class LinkGroupAdmin(NonSortableParentAdmin):
    model = LinkGroup
    inlines = [LinkInline]

    def get_model_perms(self, request):
        return {}

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id,)))

    def response_change(self, request, obj):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id,)))


class LinkGroupInline(SortableTabularInline):
    model = LinkGroup
    readonly_fields = ('title', 'edit_url',)
    fields = ('name', 'title', 'edit_url',)
    extra = 0

    def edit_url(self, obj):
        url = ''

        if obj.id is not None:
            url = "admin:%s_%s_change" % (self.model._meta.app_label,
                                          self.model._meta.model_name)
            return format_html(
                u"<a href='{}'>{}</a>",
                str(reverse(url, args=(obj.id,))), _('Edit this group')
            )
        return _('First save to edit this group')

    edit_url.short_name = 'Edit group'


@admin.register(SiteLinks)
class SiteLinksAdmin(NonSortableParentAdmin):
    model = SiteLinks
    inlines = [LinkGroupInline]


class CMSNestedContentItemInline(
    nested_admin.NestedGenericStackedInlineMixin,
    BaseContentItemInline,
):
    """
    Fluent ContentItem inline (generic FK to the page) that can host nested inlines
    defined on the ContentPlugin (e.g. steps under a Steps block).

    Keep fluent's inline_container template (not nested_admin's stacked template) so
    blocks stay in the placeholder editor. nested_admin's template adds a top-level h2
    per block type, which Jet turns into separate change-form tabs.
    """

    formset = NestedContentItemFormSet
    template = 'admin/fluent_contents/contentitem/inline_container.html'


class CMSNestedChildInline(nested_admin.NestedStackedInlineMixin, admin.StackedInline):
    """Nested inline for child models with a normal FK to their ContentItem block."""

    template = 'admin/edit_inline/stacked-nested.html'


class CMSNestedPlaceholderFieldAdmin(nested_admin.NestedModelAdminMixin, PlaceholderFieldAdmin):
    """
    Enable nested_admin for fluent-contents blocks.

    ContentItem inlines use a generic relation to the page; child inlines (Step, Quote, …)
    use a normal FK to the block model. ``get_cms_content_item_inlines`` copies plugin.inlines
    onto the generated ContentItem admin classes.
    """

    def get_extra_inlines(self):
        return [self.placeholder_inline] + get_cms_content_item_inlines(
            plugins=self.get_all_allowed_plugins(),
            base=CMSNestedContentItemInline,
        )


class StatInline(CMSNestedChildInline, SortableStackedInline):
    model = Stat
    extra = 0
    fields = ('type', 'stat_type', 'definition', 'title', 'value')

    readonly_fields = ['definition']

    def definition(self, obj):
        return getattr(Statistics, obj.type).__doc__

    def _create_formsets(self, request, obj, change):
        orig_formsets, orig_inline_instances = super()._create_formsets(
            request, obj, change
        )

        formsets = []
        inline_instances = []
        prefixes = {}

        for orig_formset, orig_inline in zip(orig_formsets, orig_inline_instances):
            if not hasattr(orig_formset, "nesting_depth"):
                orig_formset.nesting_depth = 1

            formsets.append(orig_formset)
            inline_instances.append(orig_inline)

            nested_formsets_and_inline_instances = []
            if hasattr(orig_inline, "child_inline_instances"):
                for child_inline in orig_inline.child_inline_instances:
                    nested_formsets_and_inline_instances += [
                        (orig_formset, inline, orig_inline)
                        for inline in child_inline.get_inline_instances(request, obj)
                    ]

            if getattr(orig_inline, "inlines", []):
                nested_formsets_and_inline_instances += [
                    (orig_formset, inline, orig_inline)
                    for inline in orig_inline.get_inline_instances(request, obj)
                ]

            i = 0
            while i < len(nested_formsets_and_inline_instances):
                formset, inline, parent_inline = nested_formsets_and_inline_instances[i]
                i += 1

                try:
                    has_add_permission = parent_inline.has_add_permission(request, obj)
                except TypeError:
                    # Django before 2.2 didn't require obj kwarg
                    has_add_permission = parent_inline.has_add_permission(request)

                formset_forms = list(formset.forms)

                if has_add_permission:
                    formset_forms.append(None)

                for form in formset_forms:
                    if form is not None:
                        form.parent_formset = formset
                        form_prefix = form.prefix
                        form_obj = form.instance
                        is_empty_form = False
                    else:
                        # This is the only ch<nged line. Use __prefix__ instead of empty for empty forms
                        form_prefix = formset.add_prefix("__prefix__")
                        form_obj = None
                        is_empty_form = True
                    InlineFormSet = inline.get_formset(request, form_obj)

                    # Check if we're dealing with a polymorphic instance, and if
                    # so, skip inlines for other child models
                    if hasattr(form_obj, "get_real_instance"):
                        if hasattr(InlineFormSet, "fk"):
                            rel_model = InlineFormSet.fk.remote_field.model
                            if not isinstance(form_obj, rel_model):
                                continue
                        elif not isinstance(form_obj, inline.parent_model):
                            continue

                    prefix = "{}-{}".format(
                        form_prefix, InlineFormSet.get_default_prefix()
                    )
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                    if prefixes[prefix] != 1:
                        prefix = "{}-{}".format(prefix, prefixes[prefix])

                    if hasattr(form_obj, "get_real_instance"):
                        if not isinstance(form_obj, inline.parent_model):
                            continue

                    formset_params = {
                        "instance": form_obj,
                        "prefix": prefix,
                        "queryset": inline.get_queryset(request),
                    }
                    if request.method == "POST" and not is_empty_form:
                        formset_params.update(
                            {
                                "data": request.POST.copy(),
                                "files": request.FILES,
                                "save_as_new": "_saveasnew" in request.POST,
                            }
                        )

                    nested_formset = InlineFormSet(**formset_params)

                    # We set `is_nested` to True so that we have a way
                    # to identify this formset as such and skip it if
                    # there is an error in the POST and we have to create
                    # inline admin formsets.
                    nested_formset.is_nested = True
                    nested_formset.nesting_depth = formset.nesting_depth + 1
                    nested_formset.parent_form = form

                    def user_deleted_form(request, obj, formset, index):
                        """Return whether or not the user deleted the form."""
                        return (
                            inline.has_delete_permission(request, obj)
                            and "{}-{}-DELETE".format(formset.prefix, index)
                            in request.POST
                        )

                    # Bypass validation of each view-only inline form (since the form's
                    # data won't be in request.POST), unless the form was deleted.
                    if not inline.has_change_permission(request, form_obj):
                        if "-empty-" not in nested_formset.prefix:
                            for index, initial_form in enumerate(
                                nested_formset.initial_forms
                            ):
                                if user_deleted_form(
                                    request, form_obj, nested_formset, index
                                ):
                                    continue
                                initial_form._errors = {}
                                initial_form.cleaned_data = initial_form.initial

                    # If request.method == 'POST', this is an attempted save,
                    # so we need to include the nested formsets and inline
                    # instances in the top level lists returned by this method
                    if form is not None and request.method == "POST":
                        formsets.append(nested_formset)
                        inline_instances.append(inline)

                    # nested_obj is a form or an empty formset
                    nested_obj = form or formset

                    if not hasattr(nested_obj, "nested_formsets"):
                        nested_obj.nested_formsets = []
                    if not hasattr(nested_obj, "nested_inlines"):
                        nested_obj.nested_inlines = []

                    nested_obj.nested_formsets.append(nested_formset)
                    nested_obj.nested_inlines.append(inline)

                    if hasattr(inline, "get_inline_instances"):
                        nested_formsets_and_inline_instances += [
                            (nested_formset, nested_inline, inline)
                            for nested_inline in inline.get_inline_instances(
                                request, form_obj
                            )
                        ]
                    if hasattr(inline, "child_inline_instances"):
                        for nested_child in inline.child_inline_instances:
                            nested_formsets_and_inline_instances += [
                                (nested_formset, nested_inline, nested_child)
                                for nested_inline in nested_child.get_inline_instances(
                                    request, form_obj
                                )
                            ]
        return formsets, inline_instances


class QuoteInline(CMSNestedChildInline):
    model = Quote
    extra = 1


class PersonInline(CMSNestedChildInline):
    model = Person
    extra = 1


class StepInline(CMSNestedChildInline, SortableStackedInline):
    model = Step
    extra = 0
    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }


class LogoInline(CMSNestedChildInline, SortableStackedInline):
    model = Logo
    extra = 0


class ContentLinkInline(CMSNestedChildInline, SortableStackedInline):
    model = ContentLink
    extra = 0


class GreetingInline(CMSNestedChildInline):
    model = Greeting
    extra = 0


@admin.register(ResultPage)
class ResultPageAdmin(CMSNestedPlaceholderFieldAdmin, TranslatableAdmin, NonSortableParentAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def get_prepopulated_fields(self, request, obj=None):
        # can't use `prepopulated_fields = ..` because it breaks the admin validation
        # for translated fields. This is the official django-parler workaround.
        return {
            'slug': ('title',)
        }

    list_display = 'title', 'slug', 'start_date', 'end_date'
    fields = 'title', 'slug', 'description', 'start_date', 'end_date', 'image', 'content'


@admin.register(HomePage)
class HomePageAdmin(CMSNestedPlaceholderFieldAdmin, TranslatableAdmin, SingletonModelAdmin, NonSortableParentAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fields = ('content',)


@admin.register(SitePlatformSettings)
class SitePlatformSettingsAdmin(TranslatableLabelAdminMixin, TranslatableAdmin, BasePlatformSettingsAdmin):
    readonly_fields = ['terminated_info', 'organization']

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                _('Contact'),
                {
                    'fields': (
                        'contact_email', 'contact_phone', 'terminated'
                    )
                }
            ),
            (
                _('Powered by'),
                {
                    'fields': (
                        'copyright', 'powered_by_text', 'powered_by_link', 'powered_by_logo', 'footer_banner'
                    )
                }
            ),
            (
                _('Metadata'),
                {
                    'fields': (
                        'translatable_info', 'metadata_title', 'metadata_description', 'metadata_keywords'
                    )
                }
            ),
            (
                _('Styling'),
                {
                    'fields': (
                        'logo', 'favicon',
                        'action_color', 'action_text_color', 'alternative_link_color',
                        'description_color', 'description_text_color',
                        'footer_color', 'footer_text_color',
                        'title_font', 'body_font'
                    )
                }
            ),
            (
                _('GoodUp Connect'),
                {
                    'fields': (
                        'share_activities', 'organization',
                    )
                }
            ),
        )

        if obj.terminated:
            fieldsets[0][1]['fields'] = fieldsets[0][1]['fields'] + ('terminated_info',)

        return fieldsets

    def terminated_info(self, obj):
        active_members = Member.objects.filter(is_active=True)
        return mark_safe(
            f"<div class='info_field'>"
            f"    The platform is terminated. No emails will be sent to users. "
            f"    There are {active_members.count()} active members."
            f"</div>"
        )
