import json

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from django.views.decorators.clickjacking import xframe_options_sameorigin

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from fluent_contents.models import Placeholder
from fluent_contents.rendering import render_content_items
from sorl.thumbnail.admin import AdminImageMixin

from .models import NewsItem


class NewsItemAdmin(AdminImageMixin, PlaceholderFieldAdmin):
    list_display = ('title', 'status_column', 'modification_date')
    list_filter = ('status',)
    date_hierarchy = 'publication_date'
    search_fields = ('slug', 'title')
    actions = ['make_published']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'language', 'main_image', 'contents'),
        }),
        (_('Publication settings'), {
            'fields': ('status', 'publication_date', 'publication_end_date', 'allow_comments'),
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
            url(r'^(?P<pk>\d+)/preview-canvas/$',
                self.admin_site.admin_view(
                    self.preview_canvas),
                name="{0}_{1}_preview_canvas".format(*info)),
            url(r'^(?P<pk>\d+)/get_preview/$',
                self.admin_site.admin_view(
                    self.get_preview_html),
                name="{0}_{1}_get_preview".format(*info))
        ]

        return urlpatterns + base_urls

    def get_base_object(self, pk):
        # Give a workable object, no matter whether it's a news or blogpost.
        pk = long(pk)
        if pk:
            return NewsItem.objects.get(pk=pk)
        else:
            return NewsItem()

    @xframe_options_sameorigin
    def preview_canvas(self, request, pk):
        # Avoid the proxy model stuff, allow both to work.
        blogpost = self.get_base_object(pk)
        return render(request, 'admin/news/preview_canvas.html', {
            'blogpost': blogpost,
        })

    def get_preview_html(self, request, pk):
        """
        Ajax view to return the preview.
        """
        blogpost = self.get_base_object(pk)

        # Get fluent-contents placeholder
        items = self._get_preview_items(request, blogpost)
        contents_html = mark_safe(render_content_items(request, items).html)

        status = 200
        resp = {
            'success': True,
            'title': blogpost.title,
            'contents': contents_html,
        }
        return HttpResponse(json.dumps(resp),
                            content_type='application/javascript',
                            status=status)

    def _get_preview_items(self, request, blogpost):
        """
        Construct all ContentItem models with the latest unsaved
        client-side data applied to them.

        This functionality could ideally be included in django-fluent-contents
        directly, however that would require more testing and dealing with
        the "placeholder editor" interface too, in contrast to a single
        "placeholder field", the placeholder editor allows to move
        ContentItems between placeholders.
        """
        new_items = []

        # Simulate the django-admin POST process, without saving.

        # Each ContentItem type is hosted in the Django admin as an inline
        # with a formset.
        prefixes = {}
        inline_instances = self.get_inline_instances(request)
        for FormSet, inline in zip(self.get_formsets(request),
                                   inline_instances):
            if not getattr(inline, 'is_fluent_editor_inline',
                           False) or inline.model is Placeholder:
                continue

            prefix = FormSet.get_default_prefix()
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1 or not prefix:
                prefix = "{0}-{1}".format(prefix, prefixes[prefix])

            formset = FormSet(
                data=request.POST, files=request.FILES, prefix=prefix,
                instance=blogpost, queryset=inline.queryset(request)
            )

            # Extract all items out of the formset
            # NOTE: no filtering of items for a placeholder, assume there is
            # only one PlaceholderField in the page.
            new_items += self._get_formset_objects(formset)

        # Reorder items by ordering
        new_items = sorted(new_items, key=lambda ci: ci.sort_order)

        return new_items

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

    def render_change_form(self, request, context, add=False, change=False,
                           form_url='', obj=None):
        info = self.model._meta.app_label, self.model._meta.model_name
        context.update({
            'preview_canvas_url': reverse(
                'admin:{0}_{1}_preview_canvas'.format(*info),
                kwargs={'pk': obj.pk if obj else 0}),
            'get_preview_url': reverse(
                'admin:{0}_{1}_get_preview'.format(*info),
                kwargs={'pk': obj.pk if obj else 0}),
        })
        return super(NewsItemAdmin, self).render_change_form(request, context,
                                                             add, change,
                                                             form_url, obj)

    def save_model(self, request, obj, form, change):
        # Automatically store the user in the author field.
        if not change:
            obj.author = request.user

        if not obj.publication_date:
            # auto_now_add makes the field uneditable.
            # default fills the field before the post is written (too early)
            obj.publication_date = now()
        obj.save()

    STATUS_ICONS = {
        NewsItem.PostStatus.published: 'icon-yes.gif',
        NewsItem.PostStatus.draft: 'icon-unknown.gif',
    }

    def status_column(self, blogpost):
        status = blogpost.status
        title = [rec[1] for rec in blogpost.PostStatus.choices if
                 rec[0] == status].pop()
        icon = self.STATUS_ICONS[status]
        admin_url = settings.STATIC_URL + 'admin/img/'
        return format_html(
            u'<img src="{}{}" width="10" height="10" alt="{}" title="{}" />',
            admin_url, icon, title, title
        )

    status_column.short_description = _('Status')

    def make_published(self, request, queryset):
        rows_updated = queryset.update(status=NewsItem.PostStatus.published)

        if rows_updated == 1:
            message = "1 entry was marked as published."
        else:
            message = "{0} entries were marked as published.".format(
                rows_updated)
        self.message_user(request, message)

    make_published.short_description = _("Mark selected entries as published")


admin.site.register(NewsItem, NewsItemAdmin)
