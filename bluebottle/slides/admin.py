from django.db import models

from django.contrib import admin
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from bluebottle.utils.widgets import SecureAdminURLFieldWidget

from .models import Slide


class SlideAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'sequence', 'status', 'modification_date', 'language')
    list_filter = ('status', 'language')
    date_hierarchy = 'publication_date'
    search_fields = ('slug', 'title')
    actions = ['make_published']
    model = Slide
    ordering = ('language', 'sequence', 'title')

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    fieldsets = (
        (None, {
            'fields': ('language', 'sequence', 'tab_text'),
        }),
        (_('Contents'), {
            'fields': (
                'title', 'body', 'image', 'background_image', 'video',
                'video_url', 'link_text', 'link_url', 'style'),
        }),
        (_('Publication settings'), {
            'fields': ('status', 'publication_date', 'publication_end_date'),
        }),
    )

    radio_fields = {
        'status': admin.HORIZONTAL,
        'language': admin.HORIZONTAL,
    }

    def get_base_object(self, pk):
        pk = int(pk)
        if pk:
            return Slide.objects.get(pk=pk)
        else:
            return Slide()

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
                # Before Django 1.5 that means manually constructing the
                # values as form.cleaned_data is removed.
            else:
                object = form.save(commit=False)
                # Disable actual saving code.
                object.save_base = dummy_save_base
                # Trigger any pre-save code (e.g. fetch OEmbedItem,
                # render CodeItem)
                object.save()

            all_objects.append(object)

        return all_objects

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
        Slide.SlideStatus.published: 'icon-yes.gif',
        Slide.SlideStatus.draft: 'icon-unknown.gif',
    }

    def make_published(self, request, queryset):
        rows_updated = queryset.update(status=Slide.PostStatus.published)

        if rows_updated == 1:
            message = "1 entry was marked as published."
        else:
            message = "{0} entries were marked as published.".format(
                rows_updated)
        self.message_user(request, message)

    make_published.short_description = _("Mark selected entries as published")


admin.site.register(Slide, SlideAdmin)
