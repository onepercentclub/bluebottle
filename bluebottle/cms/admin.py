from builtins import str

from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin, SortableTabularInline
from django.contrib import admin, messages
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
from bluebottle.cms.utils.color_contrast import evaluate_platform_colors
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
    readonly_fields = ['terminated_info', 'organization', 'color_contrast_panel']

    class Media:
        css = {
            'all': ('admin/css/platform_color_contrast.css',)
        }
        js = ('admin/js/platform_color_contrast.js',)

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
                        'color_contrast_panel',
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

    def color_contrast_panel(self, obj):
        return mark_safe(
            '<div id="platform-color-contrast-panel" class="platform-color-contrast">'
            '  <div class="platform-color-contrast__pairs">'
            '    <div class="platform-color-contrast__pair is-skipped" data-contrast-pair="action">'
            '      <span class="platform-color-contrast__label">Action</span>'
            '      <span class="platform-color-contrast__ratio" data-contrast-ratio>—</span>'
            '      <span class="platform-color-contrast__badge" data-contrast-badge>Not set</span>'
            '      <span class="platform-color-contrast__hint" data-contrast-hint hidden>'
            '        Text may be hard to read on this background.'
            '      </span>'
            '    </div>'
            '    <div class="platform-color-contrast__pair is-skipped" data-contrast-pair="description">'
            '      <span class="platform-color-contrast__label">Description</span>'
            '      <span class="platform-color-contrast__ratio" data-contrast-ratio>—</span>'
            '      <span class="platform-color-contrast__badge" data-contrast-badge>Not set</span>'
            '      <span class="platform-color-contrast__hint" data-contrast-hint hidden>'
            '        Text may be hard to read on this background.'
            '      </span>'
            '    </div>'
            '    <div class="platform-color-contrast__pair is-skipped" data-contrast-pair="footer">'
            '      <span class="platform-color-contrast__label">Footer</span>'
            '      <span class="platform-color-contrast__ratio" data-contrast-ratio>—</span>'
            '      <span class="platform-color-contrast__badge" data-contrast-badge>Not set</span>'
            '      <span class="platform-color-contrast__hint" data-contrast-hint hidden>'
            '        Text may be hard to read on this background.'
            '      </span>'
            '    </div>'
            '    <div class="platform-color-contrast__pair is-skipped" data-contrast-pair="link">'
            '      <span class="platform-color-contrast__label">Link</span>'
            '      <span class="platform-color-contrast__ratio" data-contrast-ratio>—</span>'
            '      <span class="platform-color-contrast__badge" data-contrast-badge>Not set</span>'
            '      <span class="platform-color-contrast__hint" data-contrast-hint hidden>'
            '        Text may be hard to read on this background.'
            '      </span>'
            '    </div>'
            '  </div>'
            '  <div class="platform-color-contrast__preview" aria-hidden="true">'
            '    <div class="platform-color-contrast__button">Button</div>'
            '    <div class="platform-color-contrast__description">Description</div>'
            '    <a class="platform-color-contrast__link" href="#" onclick="return false;">Link</a>'
            '    <div class="platform-color-contrast__footer">Footer</div>'
            '  </div>'
            '</div>'
        )

    color_contrast_panel.short_description = _('Colour contrast')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        failing = [
            result for result in evaluate_platform_colors(obj)
            if not result.passes
        ]
        if not failing:
            return
        details = ', '.join(
            '{label} ({ratio:.1f}:1)'.format(label=result.label, ratio=result.ratio)
            for result in failing
        )
        self.message_user(
            request,
            _('Colour contrast below WCAG AA for: %(pairs)s. You can still save, but text may be hard to read.') % {
                'pairs': details,
            },
            level=messages.WARNING,
        )

    def terminated_info(self, obj):
        active_members = Member.objects.filter(is_active=True)
        return mark_safe(
            f"<div class='info_field'>"
            f"    The platform is terminated. No emails will be sent to users. "
            f"    There are {active_members.count()} active members."
            f"</div>"
        )
