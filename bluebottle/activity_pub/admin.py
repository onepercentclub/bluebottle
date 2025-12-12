import requests
from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.core.exceptions import PermissionDenied, ValidationError
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
    Place,  # Add Place import
    PublicKey,
    Publish,
    Announce,
    Organization,
    Following,
    Follower, GoodDeed, CrowdFunding, DoGoodEvent,
    Recipient, SubEvent, PublishedActivity, ReceivedActivity, Accept,
)
from bluebottle.activity_pub.serializers.json_ld import OrganizationSerializer
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.members.models import Member
from bluebottle.utils.admin import admin_info_box
from bluebottle.webfinger.client import client


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
        Organization,
        GoodDeed,
        CrowdFunding,
        DoGoodEvent,
        Place,
    )

    def type(self, obj):
        return obj.get_real_instance_class().__name__ if obj.get_real_instance_class() else '-'

    list_display = ("id", "type", "iri")
    readonly_fields = ('iri', 'actor', 'pub_url')


class RecipientInline(admin.TabularInline):
    model = Recipient
    verbose_name = _("Recipient")
    verbose_name_plural = _("Recipients")
    readonly_fields = ('actor', 'send', 'republish_button')
    fields = ('actor', 'send', 'republish_button')

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def republish_button(self, obj):
        if obj.send:
            return "-"
        if not obj.id:
            return "-"
        url = reverse(
            'admin:activity_pub_activity_republish_recipient',
            args=[obj.activity_id, obj.id]
        )
        return format_html(
            '<a class="button" href="{}">{}</a>',
            url,
            _('Republish')
        )
    republish_button.short_description = _("Actions")


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
        label=_("Partner URL"),
        help_text=_("This is the website address of the partner you want to follow."),
        max_length=400
    )

    class Meta:
        model = Follow
        fields = ["iri", ]


@admin.register(Person)
class PersonAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('member', 'inbox', 'outbox', 'public_key', 'iri', 'pub_url')

    def save_formset(self, request, form, formset, change):
        if formset.model == Follow:
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    url = form.cleaned_data.get("iri")
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


@admin.register(Organization)
class OrganizationAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('organization', 'inbox', 'outbox', 'public_key', 'iri', 'pub_url')

    def save_formset(self, request, form, formset, change):
        if formset.model == Follow:
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    url = form.cleaned_data.get("iri")
                    adapter.follow(url)
        else:
            super().save_formset(request, form, formset, change)


@admin.register(Activity)
class ActivityAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    inlines = [RecipientInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/recipient/<path:recipient_id>/republish/",
                self.admin_site.admin_view(self.republish_recipient),
                name="activity_pub_activity_republish_recipient",
            ),
        ]
        return custom_urls + urls

    def republish_recipient(self, request, object_id, recipient_id):
        from django.db import connection
        from bluebottle.activity_pub.adapters import publish_to_recipient
        from bluebottle.activity_pub.models import Recipient

        activity = get_object_or_404(Activity, pk=unquote(object_id))
        recipient = get_object_or_404(Recipient, pk=unquote(recipient_id), activity=activity)

        if not request.user.has_perm("activity_pub.change_activity"):
            raise PermissionDenied

        try:
            publish_to_recipient.delay(activity, recipient, connection.tenant)
            self.message_user(
                request,
                _('Republish task queued for recipient {actor}.').format(actor=recipient.actor),
                level="success",
            )
        except Exception as e:
            self.message_user(
                request,
                _('Error queuing republish: {error}').format(error=str(e)),
                level="error",
            )

        return HttpResponseRedirect(
            reverse("admin:activity_pub_activity_change", args=[activity.pk])
        )


@admin.register(Actor)
class ActorAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')


@admin.register(Follow)
class FollowAdmin(ActivityAdmin):
    list_display = ('actor', "object")
    readonly_fields = ("actor", "object", "iri", "pub_url")


@admin.register(PublicKey)
class PublicKeyAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", 'inbox', 'outbox')


@admin.register(Publish)
class PublishAdmin(ActivityPubModelChildAdmin):
    list_display = ("id", "actor", "object")
    readonly_fields = ('iri', 'actor', 'object', 'pub_url')


@admin.register(Accept)
class AcceptAdmin(ActivityAdmin):
    list_display = ("id", "actor", "object")
    readonly_fields = ('iri', 'actor', 'object', 'pub_url')


@admin.register(Announce)
class AnnounceAdmin(ActivityAdmin):
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


class AdoptedFilter(admin.SimpleListFilter):
    title = _('Adoption Status')
    parameter_name = 'adopted'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Adopted')),
            ('no', _('Not Adopted')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(adopted_activities__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(adopted_activities__isnull=True)


class SourceFilter(admin.SimpleListFilter):
    title = _('Partner')
    parameter_name = 'partner'

    def lookups(self, request, model_admin):
        options = Organization.objects.values_list('id', 'name')
        return options

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(publishes__actor=self.value())
        return queryset


class FollowingAddForm(forms.ModelForm):
    platform_url = forms.URLField(
        label=_("Partner URL"),
        help_text=_("This is the website address of the partner you want to follow."),
    )
    default_owner = forms.ModelChoiceField(
        Member.objects.all(),
        widget=ForeignKeyRawIdWidget(Following._meta.get_field("default_owner").remote_field, admin.site),
        help_text=_("This person will be the activity manager of the activities that are adopted."),
        required=False
    )

    class Meta:
        model = Following
        fields = ['platform_url', ]
        widgets = {
            'default_owner': admin.widgets.ForeignKeyRawIdWidget(
                Following._meta.get_field('default_owner').remote_field,
                admin.site
            ),
        }

    def __init__(self, *args, **kwargs):
        # Always create a new instance when adding
        if 'instance' not in kwargs:
            kwargs['instance'] = Following()

        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if 'platform_url' in self.cleaned_data:
            try:
                client.get(self.cleaned_data['platform_url'])
            except requests.exceptions.HTTPError:
                raise ValidationError({
                    'platform_url': _(
                        "Could not determine platform information needed for subscribing. "
                        "Are you sure the url is correct?",
                    )
                })


@admin.register(Following)
class FollowingAdmin(FollowAdmin):
    list_display = ("object", "accepted")
    raw_id_fields = ('default_owner',)

    readonly_fields = ('object', 'accepted')

    def accepted(self, obj):
        """Check if this follow request has been accepted"""
        from bluebottle.activity_pub.models import Accept
        return Accept.objects.filter(object=obj).exists()

    accepted.boolean = True
    accepted.short_description = _("Accepted")

    def get_readonly_fields(self, request, obj=None):
        readonly = ['object', 'accepted', 'iri', 'actor']
        return readonly

    def get_fieldsets(self, request, obj=None):
        if not obj:
            # When adding a new Following
            return (
                (None, {
                    'fields': ('platform_url', )
                }),
            )
        else:
            # When viewing/editing an existing Following
            return (
                (None, {
                    'fields': ('object', 'accepted', )
                }),
            )

    def get_fields(self, request, obj=None):
        # This will be overridden by get_fieldsets
        fields = ['default_owner']
        if not obj:
            fields = ['connect_info', 'platform_url'] + fields
        else:
            fields = ['object', 'accepted'] + fields

        return fields

    def has_change_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = Follow.objects.all()
        platform_actor = get_platform_actor()
        if platform_actor:
            # Show Follow records where the platform is the actor (following others)
            return qs.filter(actor=platform_actor)
        return qs.none()  # No platform actor configured

    def get_form(self, request, obj=None, **kwargs):
        """Use custom form for adding new Following objects"""
        if obj is None:
            return FollowingAddForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        """Handle saving of new Following objects using adapter.follow()"""
        if not change and isinstance(form, FollowingAddForm):

            # This is a new object using our custom add form
            platform_url = form.cleaned_data['platform_url']
            default_owner = form.cleaned_data.get('default_owner')
            try:
                # Use adapter.follow to create the Follow object
                follow_obj = adapter.follow(platform_url)
                # Set the default_owner if provided
                if default_owner:
                    follow_obj.default_owner = default_owner
                    follow_obj.save()
                # Publish the Follow activity to the remote inbox
                try:
                    adapter.publish(follow_obj)
                    self.message_user(
                        request,
                        _(
                            "Follow request sent to %s. "
                            "Your platforms will be connected when the request is accepted."
                        ) % platform_url,
                        level="success"
                    )
                except Exception as publish_error:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to publish Follow {follow_obj.pk}: {str(publish_error)}", exc_info=True)
                    self.message_user(
                        request,
                        _(
                            "Follow relationship created but publishing failed: %s. "
                            "The follow request may not have been sent to the remote platform."
                        ) % str(publish_error),
                        level="warning"
                    )
                # Store the created object for response_add
                self._created_follow_obj = follow_obj
            except requests.exceptions.HTTPError:
                self.message_user(
                    request,
                    _(
                        "Could not determine platform information needed for subscribing. "
                        "Are you sure the url is correct?"
                    ),
                    level="error"
                )
            except Exception as error:
                self.message_user(
                    request,
                    _("Error creating Follow relationship: %s") % str(error),
                    level="error"
                )
        else:
            # For existing objects, use the default behavior
            super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        """Redirect to the changelist after adding"""
        if hasattr(self, '_created_follow_obj'):
            # Successfully created via adapter.follow()
            delattr(self, '_created_follow_obj')  # Clean up
            return HttpResponseRedirect(reverse('admin:activity_pub_following_changelist'))
        return super().response_add(request, obj, post_url_continue)


@admin.register(Follower)
class FollowerAdmin(FollowAdmin):
    list_display = ("platform", "accepted")
    actions = ['accept_follow_requests']
    readonly_fields = ('platform', 'accepted')
    fields = readonly_fields

    def platform(self, obj):
        return obj.actor

    platform.short_description = _("Partner")

    def get_queryset(self, request):
        qs = Follow.objects.all()
        platform_actor = get_platform_actor()
        if platform_actor:
            return qs.filter(object=platform_actor)
        return qs.none()

    def accepted(self, obj):
        """Check if this follow request has been accepted"""
        from bluebottle.activity_pub.models import Accept
        return Accept.objects.filter(object=obj).exists()

    accepted.boolean = True
    accepted.short_description = _("Accepted")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/accept/",
                self.admin_site.admin_view(self.accept_follow_request),
                name="activity_pub_follower_accept",
            ),
        ]
        return custom_urls + urls

    def accept_follow_request(self, request, object_id):
        """Accept a single follow request"""
        from bluebottle.activity_pub.models import Accept, Follow

        follow = get_object_or_404(Follow, pk=unquote(object_id))
        platform_actor = get_platform_actor()

        if not platform_actor:
            self.message_user(request, "No platform actor configured", level="error")
            return HttpResponseRedirect(
                reverse("admin:activity_pub_follower_change", args=[follow.pk])
            )

        # Check if already accepted
        if Accept.objects.filter(object=follow).exists():
            self.message_user(
                request,
                f"Follow request from {follow.actor} has already been accepted",
                level="info"
            )
        else:
            # Create Accept object
            Accept.objects.create(
                actor=platform_actor,
                object=follow
            )
            self.message_user(
                request,
                f"Successfully accepted follow request from {follow.actor}",
                level="success"
            )

        return HttpResponseRedirect(reverse('admin:activity_pub_follower_changelist'))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add accept button context"""
        extra_context = extra_context or {}

        if object_id:
            from bluebottle.activity_pub.models import Accept, Follow
            follow = get_object_or_404(Follow, pk=unquote(object_id))
            extra_context['is_accepted'] = Accept.objects.filter(object=follow).exists()
            extra_context['accept_url'] = reverse('admin:activity_pub_follower_accept', args=[object_id])

        return super().change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow viewing but not actual changing
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def accept_follow_requests(self, request, queryset):
        """Accept selected follow requests"""
        from bluebottle.activity_pub.models import Accept

        platform_actor = get_platform_actor()
        if not platform_actor:
            self.message_user(request, "No platform actor configured", level="error")
            return

        accepted_count = 0
        already_accepted_count = 0

        for follow in queryset:
            # Check if already accepted
            if Accept.objects.filter(object=follow).exists():
                already_accepted_count += 1
                continue

            # Create Accept object
            Accept.objects.create(
                actor=platform_actor,
                object=follow
            )
            accepted_count += 1

        if accepted_count > 0:
            self.message_user(
                request,
                f"Successfully accepted {accepted_count} follow request(s)",
                level="success"
            )

        if already_accepted_count > 0:
            self.message_user(
                request,
                f"{already_accepted_count} follow request(s) were already accepted",
                level="info"
            )

    accept_follow_requests.short_description = "Accept selected follow requests"


@admin.register(Place)
class PlaceAdmin(ActivityPubModelChildAdmin):
    list_display = (
        "name",
        "latitude",
        "longitude"
    )
    search_fields = ['name', ]
    readonly_fields = ("pub_url",)

    fieldsets = (
        (None, {
            'fields': ('name', 'pub_url')
        }),
        (_('Coordinates'), {
            'fields': ('latitude', 'longitude')
        }),
    )


class PlaceInline(admin.StackedInline):
    model = Place
    extra = 0
    max_num = 1
    verbose_name = _("Location")
    verbose_name_plural = _("Locations")
    fields = (
        'name',
        'street_address',
        'postal_code',
        'locality',
        'region',
        'country',
        'country_code',
        'latitude',
        'longitude'
    )


class EventAdminMixin:
    list_display = (
        "name",
        "source",
        "adopted",
    )
    readonly_fields = (
        "name",
        "display_description",
        "display_image",
        "source",
    )
    fields = readonly_fields
    list_filter = [AdoptedFilter, SourceFilter]

    def adopted(self, obj):
        return obj.adopted

    adopted.boolean = True
    adopted.short_description = _("Adopted")

    inlines = []

    def source(self, obj):
        return obj.source
    source.short_description = _("Partner")

    def display_description(self, obj):
        return format_html(
            '<div style="display: table-cell; border-left:1px solid #aaa; padding: 0 12px">' + obj.summary + "</div>"
        )

    display_description.short_description = _("Description")

    def display_image(self, obj):
        return format_html(
            '<img src="{}" style="max-height: 300px; max-width: 600px;" />', obj.image.url
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
                "This activity has already been adopted.",
                level="warning",
            )
            return HttpResponseRedirect(
                reverse("admin:activity_pub_event_change", args=[event.pk])
            )

        try:
            activity = adapter.adopt(event, request)

            self.message_user(
                request,
                f'Successfully created Activity "{activity.title}" from Event.',
                level="success",
            )
            return HttpResponseRedirect(
                reverse("admin:activities_activity_change", args=[activity.pk])
            )

        except Exception as e:
            self.message_user(request, f"Error creating activity: {str(e)}", level="error")
            return HttpResponseRedirect(
                reverse("admin:activity_pub_event_change", args=[event.pk])
            )


@admin.register(Event)
class EventPolymorphicAdmin(EventAdminMixin, PolymorphicParentModelAdmin):
    base_model = Event
    child_models = (
        GoodDeed,
        CrowdFunding,
        DoGoodEvent,

    )
    list_filter = [AdoptedFilter, SourceFilter, PolymorphicChildModelFilter]

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name if obj.get_real_instance_class() else '-'

    list_display = ("name", "type", "source", "adopted")

    def name_link(self, obj):
        """Generate the name as a link to the polymorphic child admin."""
        real_instance = obj.get_real_instance()
        model_name = real_instance._meta.model_name
        app_label = real_instance._meta.app_label
        change_url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', change_url, obj.name)

    name_link.short_description = _("Activity title")
    name_link.admin_order_field = "name"  # Allow sorting by name


@admin.register(PublishedActivity)
class PublishedActivityAdmin(EventPolymorphicAdmin):
    model = PublishedActivity
    list_display = ("name_link", "type")
    list_display_links = ("name_link",)

    def get_queryset(self, request):
        return Event.objects.filter(iri__isnull=True)


@admin.register(ReceivedActivity)
class ReceivedActivityAdmin(EventPolymorphicAdmin):
    model = ReceivedActivity
    list_display = ("name_link", "type", "source", "adopted")
    list_display_links = ("name_link",)

    def source(self, obj):
        return obj.source
    source.short_description = _('Partner')

    def get_queryset(self, request):
        return Event.objects.filter(iri__isnull=False)


class EventChildAdmin(EventAdminMixin, ActivityPubModelChildAdmin):
    change_form_template = 'admin/activity_pub/event/change_form.html'
    base_model = Event
    fields = ('adopt_info',) + EventAdminMixin.fields

    readonly_fields = ('adopt_info',) + EventAdminMixin.readonly_fields

    def adopt_info(self, obj):
        return admin_info_box(
            _('You can make changes to this activity after you adopt it '
              'which will create a draft version of this activity.'))


@admin.register(GoodDeed)
class GoodDeedAdmin(EventChildAdmin):
    base_model = Event
    model = GoodDeed
    readonly_fields = EventChildAdmin.readonly_fields + (
        'start_time',
        'end_time',
    )
    fields = readonly_fields


@admin.register(CrowdFunding)
class CrowdFundingAdmin(EventChildAdmin):
    base_model = Event
    model = GoodDeed
    readonly_fields = EventChildAdmin.readonly_fields + (
        'end_time',
        'target'
    )
    fields = readonly_fields


class SubEventInline(admin.TabularInline):
    model = SubEvent
    fk_name = 'parent'
    verbose_name_plural = _('Slots')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    readonly_fields = [
        'start_time',
        'end_time',
        'display_location'
    ]

    fields = readonly_fields

    extra = 0

    def display_location(self, obj):
        if obj.location:
            return obj.location.name or obj.location.address
    display_location.short_description = _('Location')


@admin.register(DoGoodEvent)
class DoGoodEventAdmin(EventChildAdmin):
    base_model = Event
    model = DoGoodEvent

    inlines = [SubEventInline] + EventChildAdmin.inlines

    def get_inline_instances(self, request, obj=None):
        inlines = super(DoGoodEventAdmin, self).get_inline_instances(request, obj)
        if obj.sub_event.count():
            return inlines
        else:
            return []

    readonly_fields = EventChildAdmin.readonly_fields + (
        'start_time',
        'end_time',
        'registration_deadline',
    )
    fields = readonly_fields
