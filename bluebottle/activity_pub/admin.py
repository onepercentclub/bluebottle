from django.contrib import admin
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicParentModelAdmin,
)

from bluebottle.activity_pub.models import Actor, Person, Inbox, Activity, Outbox, ActivityPubModel, Follow, PublicKey


@admin.register(ActivityPubModel)
class ActivityPubModelAdmin(PolymorphicParentModelAdmin):
    base_model = ActivityPubModel
    child_models = (
        Person,
        Activity,
        Outbox,
        Inbox,
        Actor,
        Follow,
        PublicKey
    )

    list_display = ('id', 'inbox', 'outbox')


class ActivityPubModelChildAdmin(PolymorphicChildModelAdmin):
    base_model = ActivityPubModel


@admin.register(Inbox)
class InboxAdmin(ActivityPubModelChildAdmin):
    pass


@admin.register(Outbox)
class OutboxAdmin(ActivityPubModelChildAdmin):
    pass


@admin.register(Person)
class PersonAdmin(ActivityPubModelChildAdmin):
    list_display = ('id', 'inbox', 'outbox')
    readonly_fields = ('member', 'inbox', 'outbox', 'public_key', 'url')


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
