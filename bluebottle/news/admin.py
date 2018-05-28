from django.conf.urls import url
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from sorl.thumbnail.admin import AdminImageMixin

from .models import NewsItem


class NewsItemAdmin(AdminImageMixin, PlaceholderFieldAdmin):
    list_display = ('title', 'online', 'status', 'publication_date')
    list_filter = ('status',)
    date_hierarchy = 'publication_date'
    search_fields = ('slug', 'title')
    actions = ['make_published']
    raw_id_fields = ['author']
    readonly_fields = ('online', )

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
        pk = long(pk)
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

    STATUS_ICONS = {
        NewsItem.PostStatus.published: 'icon-yes.gif',
        NewsItem.PostStatus.draft: 'icon-unknown.gif',
    }

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
