import json
from io import BytesIO

import requests
from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Activity,
    ActivityPubModel,
    Actor,
    Event,
    Follow,
    Inbox,
    Outbox,
    Person,
    PublicKey,
    Publish,
    Announce,
    PubOrganization,
)
from bluebottle.activity_pub.serializers import OrganizationSerializer
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image


@admin.register(ActivityPubModel)
class ActivityPubModelAdmin(PolymorphicParentModelAdmin):
    base_model = ActivityPubModel
    list_filter = [PolymorphicChildModelFilter]
    child_models = (
        Person,
        Activity,
        Outbox,
        Inbox,
        Actor,
        Follow,
        PublicKey,
        Publish,
        Announce,
        Event,
        PubOrganization,
    )

    def type(self, obj):
        return obj.get_real_instance_class().__name__

    list_display = ("id", "type", "url")


class ActivityPubModelChildAdmin(PolymorphicChildModelAdmin):
    base_model = ActivityPubModel
    readonly_fields = ["pub_url", ]


@admin.register(Inbox)
class InboxAdmin(ActivityPubModelChildAdmin):
    pass


@admin.register(Outbox)
class OutboxAdmin(ActivityPubModelChildAdmin):
    pass


class FollowForm(forms.ModelForm):
    url = forms.URLField(
        label=_("Organisation URL"),
        help_text="Enter the ActivityPub URL of the organisation to follow",
        max_length=400
    )

    class Meta:
        model = Follow
        fields = ["url", "object"]


class FollowingInline(admin.StackedInline):
    verbose_name = "Following"
    verbose_name_plural = "Following"
    model = Follow
    extra = 1
    fk_name = "actor"
    form = FollowForm
    readonly_fields = ("actor",)

    def get_formset(self, request, obj=None, **kwargs):
        """Override to use different forms for new vs existing objects"""
        formset = super().get_formset(request, obj, **kwargs)

        class CustomFormSet(formset):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Initialize required attributes
                self.new_objects = []
                self.changed_objects = []
                self.deleted_objects = []

                for form in self.forms:
                    if form.instance and form.instance.pk:
                        form.fields["url"].widget = forms.widgets.HiddenInput()
                    else:
                        form.fields["object"].required = False
                        form.fields["object"].widget = forms.widgets.HiddenInput()

            def save(self, commit=True):
                return []

        return CustomFormSet

    def has_add_permission(self, request, obj=None):
        return obj is not None

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FollowersInline(admin.StackedInline):
    verbose_name = "Follower"
    verbose_name_plural = "Followers"
    model = Follow
    fk_name = "object"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_formset(self, request, obj=None, **kwargs):
        """Override to prevent normal formset saving"""
        formset = super().get_formset(request, obj, **kwargs)

        class CustomFormSet(formset):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Initialize required attributes
                self.new_objects = []
                self.changed_objects = []
                self.deleted_objects = []

            def save(self, commit=True):
                return []

        return CustomFormSet


@admin.register(Person)
class PersonAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('member', 'inbox', 'outbox', 'public_key', 'url', 'pub_url')
    inlines = [FollowingInline, FollowersInline]

    def save_formset(self, request, form, formset, change):
        if formset.model == Follow:
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    url = form.cleaned_data.get("url")
                    actor = form.instance.actor
                    if url:
                        try:
                            target_actor = adapter.sync(url, serializer=OrganizationSerializer)
                            follow = Follow.objects.create(actor=actor, object=target_actor)
                            try:
                                adapter.publish(follow)
                                self.message_user(
                                    request,
                                    f"Successfully created and published Follow relationship to {url}",
                                )
                            except Exception as e:
                                self.message_user(
                                    request,
                                    f"Follow created but publishing failed: {str(e)}",
                                    level="warning",
                                )
                        except Exception as e:
                            self.message_user(
                                request,
                                f"Error processing Follow form: {str(e)}",
                                level="error",
                            )
        else:
            super().save_formset(request, form, formset, change)


@admin.register(PubOrganization)
class PubOrganizationAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('organization', 'inbox', 'outbox', 'public_key', 'url', 'pub_url')
    inlines = [FollowingInline, FollowersInline]

    def save_formset(self, request, form, formset, change):
        if formset.model == Follow:
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    url = form.cleaned_data.get("url")
                    actor = form.instance.actor
                    if url:
                        try:
                            try:
                                target_actor = adapter.sync(url, serializer=OrganizationSerializer)
                                follow = Follow.objects.create(actor=actor, object=target_actor)
                                try:
                                    adapter.publish(follow)
                                    self.message_user(
                                        request,
                                        f"Successfully created and published Follow relationship to {url}",
                                    )
                                except Exception as e:
                                    self.message_user(
                                        request,
                                        f"Follow created but publishing failed: {str(e)}",
                                        level="warning",
                                    )
                            except Exception as e:
                                self.message_user(
                                    request,
                                    f"Error creating Follow: {str(e)}",
                                    level="error",
                                )
                        except Exception as e:
                            self.message_user(
                                request,
                                f"Error processing Follow form: {str(e)}",
                                level="error",
                            )
        else:
            super().save_formset(request, form, formset, change)


@admin.register(Activity)
class ActivityAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')


@admin.register(Actor)
class ActorAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')


@admin.register(Follow)
class FollowAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ("actor", "object", "url", "pub_url")


@admin.register(PublicKey)
class PublicKeyAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", 'inbox', 'outbox')


@admin.register(Publish)
class PublishAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", "actor", "object")


@admin.register(Announce)
class AnnounceAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", "actor", "object")


class AnnouncementInline(admin.StackedInline):
    verbose_name = _("Adoption")
    verbose_name_plural = _("Adoptions")
    model = Announce
    extra = 0
    fk_name = "object"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(ActivityPubModelChildAdmin):
    list_display = (
        "name",
        "organizer",
        "start_date",
        "end_date",
        "organizer",
    )
    readonly_fields = (
        "name",
        "display_description",
        "display_image",
        "start_date",
        "end_date",
        "organizer",
        "actor",
        "activity",
        "url",
    )
    fields = readonly_fields
    inlines = [AnnouncementInline]

    def display_description(self, obj):
        return format_html(
            '<div style="display: table-cell">' + obj.description + "</div>"
        )
    display_description.short_description = _("Description")

    def display_image(self, obj):
        return format_html(
            '<img src="{}" style="max-height: 300px; max-width: 600px;>" />', obj.image
        )
    display_image.short_description = _("Image")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/adopt/",
                self.admin_site.admin_view(self.adopt_event),
                name="activity_pub_event_adopt",
            ),
        ]
        return custom_urls + urls

    def adopt_event(self, request, object_id):
        """
        Create a Deed from the Event information
        """
        if not request.user.has_perm("deeds.add_deed"):
            raise PermissionDenied

        event = get_object_or_404(Event, pk=unquote(object_id))

        if event.activity:
            self.message_user(
                request,
                "This event has already been adopted as a Deed.",
                level="warning",
            )
            return HttpResponseRedirect(
                reverse("admin:activity_pub_event_change", args=[event.pk])
            )

        try:
            deed = Deed.objects.create(
                owner=request.user,
                title=event.name,
                description=json.dumps({"html": event.description, "delta": ""}),
                start=event.start_date,
                end=event.end_date,
                status="draft",
            )

            if event.image:
                try:
                    response = requests.get(event.image, timeout=30)
                    response.raise_for_status()

                    image = Image(owner=request.user)

                    import time

                    filename = f"event_{event.pk}_{int(time.time())}.jpg"

                    image.file.save(filename, File(BytesIO(response.content)))

                    deed.image = image
                    deed.save()

                except Exception as e:
                    self.message_user(
                        request,
                        f"Warning: Could not download image from {event.image}: {str(e)}",
                        level="warning",
                    )

            event.activity = deed
            event.save()

            self.message_user(
                request,
                f'Successfully created Deed "{deed.title}" from Event "{event.name}".',
                level="success",
            )

            return HttpResponseRedirect(
                reverse("admin:deeds_deed_change", args=[deed.pk])
            )

        except Exception as e:
            self.message_user(request, f"Error creating Deed: {str(e)}", level="error")
            return HttpResponseRedirect(
                reverse("admin:activity_pub_event_change", args=[event.pk])
            )
