import json

from adminsortable.admin import NonSortableParentAdmin
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import Form
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import re_path
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from fluent_contents.rendering import render_placeholder
from parler.admin import TranslatableAdmin

from .models import Page
from .models import PlatformPage
from .utils import export_page_to_dict, import_pages_from_data


class PageImportForm(Form):
    json_file = forms.FileField(label=_('JSON file'), help_text=_('Select a JSON file exported from another platform'))


@admin.register(Page)
class PageAdmin(PlaceholderFieldAdmin):
    model = Page
    list_display = ('title', 'slug', 'online', 'status',
                    'publication_date', 'language')
    list_filter = ('status', 'language')
    date_hierarchy = 'publication_date'
    search_fields = ('slug', 'title')
    actions = ['make_published', 'export_selected']
    ordering = ('language', 'slug', 'title')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author', )
    readonly_fields = ('online', )

    # Reserved slugs for platform pages
    RESERVED_SLUGS = ['terms', 'terms-and-conditions', 'privacy', 'start']

    radio_fields = {
        'status': admin.HORIZONTAL,
        'language': admin.HORIZONTAL,
    }

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'language', 'full_page', 'show_title', 'body'),
        }),
        (_('Publication settings'), {
            'fields': ('status', 'publication_date', 'publication_end_date', 'online'),
        }),
    )

    def online(self, obj):
        if (
            obj.status == 'published' and
            obj.publication_date and
            obj.publication_date < now() and
            (obj.publication_end_date is None or obj.publication_end_date > now())
        ):
            return format_html('<span class="admin-label admin-label-green">{}</span>', _("Online"))
        return format_html('<span class="admin-label admin-label-gray">{}</span>', _("Offline"))

    online.help_text = _("Is this item currently visible online or not.")

    def preview_slide(self, obj):
        return obj.body

    def get_urls(self):
        # Include extra API views in this admin page
        base_urls = super(PageAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            re_path(
                r'^(?P<pk>\d+)/preview/$',
                self.admin_site.admin_view(
                    self.preview_canvas
                ),
                name="{0}_{1}_preview".format(*info)
            ),
            re_path(
                r'^(?P<pk>\d+)/export/$',
                self.admin_site.admin_view(
                    self.export_page
                ),
                name="{0}_{1}_export".format(*info)
            ),
            re_path(
                r'^import/$',
                self.admin_site.admin_view(
                    self.import_pages
                ),
                name="{0}_{1}_import".format(*info)
            ),
        ]

        return urlpatterns + base_urls

    def get_base_object(self, pk):
        pk = int(pk)
        if pk:
            return Page.objects.get(pk=pk)
        else:
            return Page()

    @xframe_options_sameorigin
    def preview_canvas(self, request, pk):
        # Avoid the proxy model stuff, allow both to work.
        page = self.get_base_object(pk)
        return render(request, 'admin/pages/preview_canvas.html', {
            'page': page,
            'body': mark_safe(render_placeholder(request, page.body).html)
        })

    def _get_formset_objects(self, formset):
        all_objects = []

        def dummy_save_base(*args, **kwargs):
            pass

        # Based on BaseModelFormSet.save_existing_objects()
        # +  BaseModelFormSet.save_new_objects()
        for form in formset.initial_forms + formset.extra_forms:
            if formset.can_delete and formset._should_delete_form(form):
                continue

            if not form.is_valid():
                object = form.instance  # Keep old data
                # TODO: merge validated fields into object.
                # Before Django 1.5 that means manually constructing the values as form.cleaned_data is removed.
            else:
                object = form.save(commit=False)
                object.save_base = dummy_save_base  # Disable actual saving code.
                object.save()  # Trigger any pre-save code (e.g. fetch OEmbedItem, render CodeItem)

            all_objects.append(object)

        return all_objects

    def render_change_form(self, request, context, add=False, change=False,
                           form_url='', obj=None):
        info = self.model._meta.app_label, self.model._meta.model_name
        context.update({
            'preview_canvas_url': reverse('admin:{0}_{1}_preview'.format(*info),
                                          kwargs={'pk': obj.pk if obj else 0}),
        })
        if change and obj and request.user.is_superuser:
            context.update({
                'export_url': reverse('admin:{0}_{1}_export'.format(*info),
                                      kwargs={'pk': obj.pk}),
            })
        return super(PageAdmin, self).render_change_form(request, context, add,
                                                         change, form_url, obj)

    def save_model(self, request, obj, form, change):
        # Check if slug is reserved for platform pages
        if obj.slug in self.RESERVED_SLUGS:
            platform_page_url = reverse('admin:pages_platformpage_changelist')
            message = format_html(
                _('You are trying to create a platform page. Please do so at <a href="{}">Platform pages</a>.'),
                platform_page_url
            )
            messages.error(request, message)
            # Store flag to prevent saving and redirect
            request._reserved_slug_error = True
            return

        # Automatically store the user in the author field.
        if not obj.author:
            obj.author = request.user
        obj.save()

    def response_add(self, request, obj, post_url_continue=None):
        # Check if we need to redirect due to reserved slug
        if getattr(request, '_reserved_slug_error', False):
            page_list_url = reverse('admin:pages_page_changelist')
            return HttpResponseRedirect(page_list_url)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        # Check if we need to redirect due to reserved slug
        if getattr(request, '_reserved_slug_error', False):
            page_list_url = reverse('admin:pages_page_changelist')
            return HttpResponseRedirect(page_list_url)
        return super().response_change(request, obj)

    STATUS_ICONS = {
        Page.PageStatus.published: 'icon-yes.gif',
        Page.PageStatus.draft: 'icon-unknown.gif',
    }

    def status_column(self, page):
        status = page.status
        title = [rec[1] for rec in page.PageStatus.choices if
                 rec[0] == status].pop()
        icon = self.STATUS_ICONS[status]
        admin = settings.STATIC_URL + 'admin/img/'
        return format_html(
            u'<img src="{}{}" width="10" height="10" alt="{}" title="{}" />',
            admin, icon, title, title)

    status_column.short_description = _('Status')

    def make_published(self, request, queryset):
        rows_updated = queryset.update(status=Page.PageStatus.published)

        if rows_updated == 1:
            message = "1 entry was marked as published."
        else:
            message = "{0} entries were marked as published.".format(
                rows_updated)
        self.message_user(request, message)

    make_published.short_description = _("Mark selected entries as published")

    def export_selected(self, request, queryset):
        """Export selected pages to JSON file."""
        export_data = []
        for page in queryset:
            export_data.append(export_page_to_dict(page))

        if not export_data:
            self.message_user(request, _("No pages were selected."), messages.WARNING)
            return

        # Create JSON response
        response = HttpResponse(
            json.dumps(export_data, indent=2, cls=DjangoJSONEncoder),
            content_type='application/json'
        )
        filename = f"pages_export_{now().strftime('%Y%m%d_%H%M%S')}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    export_selected.short_description = _("Export selected pages")

    def export_page(self, request, pk):
        """Export a single page to JSON file."""
        page = self.get_object(request, pk)
        if page is None:
            from django.contrib.admin.exceptions import DisallowedModelAdminToField
            raise DisallowedModelAdminToField(
                "Page object with primary key '%s' does not exist." % pk
            )

        # Export page data using utility function (request is used for absolute image URLs)
        export_data = [export_page_to_dict(page)]

        # Create JSON response
        response = HttpResponse(
            json.dumps(export_data, indent=2, cls=DjangoJSONEncoder),
            content_type='application/json'
        )
        filename = f"page_{page.slug}_{page.pk}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def import_pages(self, request):
        """Import pages from JSON file."""
        if request.method == 'POST':
            form = PageImportForm(request.POST, request.FILES)
            if form.is_valid():
                json_file = form.cleaned_data['json_file']
                try:
                    json_file.seek(0)  # Reset file pointer
                    data = json.load(json_file)
                    result = import_pages_from_data(data)

                    message = render_to_string(
                        'admin/pages/page/import_message.html',
                        {'result': result},
                        request=request
                    ).strip()

                    if result['imported'] > 0 or result['updated'] > 0:
                        messages.success(request, message)
                    else:
                        messages.info(request, message)

                    total_count = result['imported'] + result['updated']
                    last_page = result['last_item']
                    if total_count == 1 and last_page:
                        return redirect('admin:pages_page_change', last_page.pk)
                    else:
                        return redirect('admin:pages_page_changelist')
                except json.JSONDecodeError:
                    messages.error(request, _("Invalid JSON file. Please check the file format."))
                except Exception as e:
                    messages.error(request, _("Error importing pages: {0}").format(str(e)))
        else:
            form = PageImportForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'title': _('Import pages'),
        }
        return render(request, 'admin/pages/page/import.html', context)

    def changelist_view(self, request, extra_context=None):
        """Override to add import URL to context."""
        extra_context = extra_context or {}
        info = self.model._meta.app_label, self.model._meta.model_name
        if request.user.is_superuser:
            extra_context['import_url'] = reverse('admin:{0}_{1}_import'.format(*info))
        return super(PageAdmin, self).changelist_view(request, extra_context)


@admin.register(PlatformPage)
class PlatformPageAdmin(TranslatableAdmin, PlaceholderFieldAdmin, NonSortableParentAdmin):
    model = Page
    list_display = ('slug', 'title',)
    fields = ['title', 'slug', 'body']

    empty_value_display = '-empty-'
