import json

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import re_path
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, ngettext
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin

from bluebottle.utils.models import PublishedStatus
from .models import NewsItem
from .utils import export_news_item_to_dict, import_news_items_from_data


class NewsItemImportForm(Form):
    json_file = forms.FileField(label=_('JSON file'), help_text=_('Select a JSON file exported from another platform'))


class NewsItemAdmin(PlaceholderFieldAdmin):
    list_display = ('title', 'online', 'status', 'publication_date')
    list_filter = ('status',)
    date_hierarchy = 'publication_date'
    search_fields = ('slug', 'title')
    actions = ['make_published', 'export_selected']
    raw_id_fields = ['author']
    readonly_fields = ('online',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'language', 'main_image', 'contents'),
        }),
        (_('Publication settings'), {
            'fields': ('status', 'publication_date', 'publication_end_date', 'online'),
        }),
    )

    prepopulated_fields = {'slug': ('title',)}
    radio_fields = {
        'status': admin.HORIZONTAL,
        'language': admin.HORIZONTAL,
    }

    def get_urls(self):
        # Include extra API views in this admin page
        base_urls = super(NewsItemAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            re_path(
                r'^(?P<pk>\d+)/export/$',
                self.admin_site.admin_view(
                    self.export_news_item
                ),
                name="{0}_{1}_export".format(*info)
            ),
            re_path(
                r'^import/$',
                self.admin_site.admin_view(
                    self.import_news_items
                ),
                name="{0}_{1}_import".format(*info)
            ),
        ]

        return urlpatterns + base_urls

    def online(self, obj):
        if obj.status == 'published' and \
            obj.publication_date and \
            obj.publication_date < now() and \
            (obj.publication_end_date is None or obj.publication_end_date > now()):
            return format_html('<span class="admin-label admin-label-green">{}</span>', _("Online"))
        return format_html('<span class="admin-label admin-label-gray">{}</span>', _("Offline"))

    online.help_text = _("Is this item currently visible online or not.")

    def get_base_object(self, pk):
        # Give a workable object, no matter whether it's a news or blogpost.
        pk = int(pk)
        if pk:
            return NewsItem.objects.get(pk=pk)
        else:
            return NewsItem()

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
                obj = form.instance  # Keep old data
                # TODO: merge validated fields into object.
                # Before Django 1.5 that means manually constructing the values
                # as form.cleaned_data is removed.
            else:
                obj = form.save(commit=False)
                obj.save_base = dummy_save_base  # Disable actual saving code.
                # Trigger any pre-save code (e.g. fetch OEmbedItem,
                # render CodeItem)
                obj.save()

            all_objects.append(obj)

        return all_objects

    def save_model(self, request, obj, form, change):
        # Automatically store the user in the author field.
        if not obj.author:
            obj.author = request.user

        if not obj.publication_date:
            # auto_now_add makes the field uneditable.
            # default fills the field before the post is written (too early)
            obj.publication_date = now()
        obj.save()

    def render_change_form(self, request, context, add=False, change=False,
                           form_url='', obj=None):
        info = self.model._meta.app_label, self.model._meta.model_name
        if change and obj and request.user.is_superuser:
            context.update({
                'export_url': reverse('admin:{0}_{1}_export'.format(*info),
                                      kwargs={'pk': obj.pk}),
            })
        return super(NewsItemAdmin, self).render_change_form(request, context, add,
                                                             change, form_url, obj)

    STATUS_ICONS = {
        PublishedStatus.published: 'icon-yes.gif',
        PublishedStatus.draft: 'icon-unknown.gif',
    }

    def make_published(self, request, queryset):
        rows_updated = queryset.update(status=PublishedStatus.published)

        if rows_updated == 1:
            message = "1 entry was marked as published."
        else:
            message = "{0} entries were marked as published.".format(
                rows_updated)
        self.message_user(request, message)

    make_published.short_description = _("Mark selected entries as published")

    def export_selected(self, request, queryset):
        """Export selected news items to JSON file."""
        export_data = []
        for news_item in queryset:
            export_data.append(export_news_item_to_dict(news_item, request=request))

        if not export_data:
            self.message_user(request, _("No news items were selected."), messages.WARNING)
            return

        # Create JSON response
        response = HttpResponse(
            json.dumps(export_data, indent=2, cls=DjangoJSONEncoder),
            content_type='application/json'
        )
        filename = f"news_items_export_{now().strftime('%Y%m%d_%H%M%S')}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    export_selected.short_description = _("Export selected news items")

    def export_news_item(self, request, pk):
        """Export a single news item to JSON file."""
        news_item = self.get_object(request, pk)
        if news_item is None:
            from django.contrib.admin.exceptions import DisallowedModelAdminToField
            raise DisallowedModelAdminToField(
                "NewsItem object with primary key '%s' does not exist." % pk
            )

        # Export news item data using utility function (request is used for absolute image URLs)
        export_data = [export_news_item_to_dict(news_item)]

        # Create JSON response
        response = HttpResponse(
            json.dumps(export_data, indent=2, cls=DjangoJSONEncoder),
            content_type='application/json'
        )
        filename = f"news_item_{news_item.slug}_{news_item.pk}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def import_news_items(self, request):
        """Import news items from JSON file."""
        if request.method == 'POST':
            form = NewsItemImportForm(request.POST, request.FILES)
            if form.is_valid():
                json_file = form.cleaned_data['json_file']
                try:
                    json_file.seek(0)
                    data = json.load(json_file)

                    # Import news items using utility function
                    result = import_news_items_from_data(data)
                    imported_count = result['imported']
                    updated_count = result['updated']
                    last_item = result['last_item']

                    # Show success message
                    parts = []
                    if imported_count > 0:
                        parts.append(ngettext(
                            "1 news item was imported",
                            "{0} news items were imported",
                            imported_count
                        ).format(imported_count))
                    if updated_count > 0:
                        parts.append(ngettext(
                            "1 news item was updated",
                            "{0} news items were updated",
                            updated_count
                        ).format(updated_count))

                    if parts:
                        messages.success(request, ". ".join(parts) + ".")
                    else:
                        messages.info(request, _("No news items were imported or updated."))

                    # Redirect to the item if only one was imported/updated, otherwise changelist
                    total_count = imported_count + updated_count
                    if total_count == 1 and last_item:
                        return redirect('admin:news_newsitem_change', last_item.pk)
                    else:
                        return redirect('admin:news_newsitem_changelist')
                except json.JSONDecodeError:
                    messages.error(request, _("Invalid JSON file. Please check the file format."))
                except Exception as e:
                    messages.error(request, _("Error importing news items: {0}").format(str(e)))
        else:
            form = NewsItemImportForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'title': _('Import news items'),
        }
        return render(request, 'admin/news/newsitem/import.html', context)

    def changelist_view(self, request, extra_context=None):
        """Override to add import URL to context."""
        extra_context = extra_context or {}
        info = self.model._meta.app_label, self.model._meta.model_name
        if request.user.is_superuser:
            extra_context['import_url'] = reverse('admin:{0}_{1}_import'.format(*info))
        return super(NewsItemAdmin, self).changelist_view(request, extra_context)


admin.site.register(NewsItem, NewsItemAdmin)
