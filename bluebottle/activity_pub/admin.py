from django import forms
from django.contrib import admin
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
)
from bluebottle.activity_pub.serializers import (
    PersonSerializer,
)


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
        Event,
    )

    def type(self, obj):
        return obj.get_real_instance_class().__name__

    list_display = ("id", "type", "url")


class ActivityPubModelChildAdmin(PolymorphicChildModelAdmin):
    base_model = ActivityPubModel


@admin.register(Inbox)
class InboxAdmin(ActivityPubModelChildAdmin):
    pass


@admin.register(Outbox)
class OutboxAdmin(ActivityPubModelChildAdmin):
    pass


class FollowForm(forms.ModelForm):
    url = forms.URLField(help_text="Enter the URL of the Actor to follow", max_length=400)

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
                # Don't save through normal formset process
                # The PersonAdmin.save_formset will handle this
                return []

        return CustomFormSet


@admin.register(Person)
class PersonAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('member', 'inbox', 'outbox', 'public_key', 'url')
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
                                target_actor = adapter.sync(
                                    url, serializer=PersonSerializer
                                )
                                follow = Follow.objects.create(
                                    actor=actor, object=target_actor
                                )
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


@admin.register(PublicKey)
class PublicKeyAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')


@admin.register(Publish)
class PublishAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", "inbox", "outbox")


@admin.register(Event)
class EventAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", "name", "platform", "start_date", "end_date", "organizer")
    readonly_fields = (
        "name",
        "description",
        "platform",
        "image",
        "start_date",
        "end_date",
        "organizer",
        "activity",
        "url",
    )
