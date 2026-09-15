from django.db import models, connection
from django.utils.translation import gettext_lazy as _

from multiselectfield import MultiSelectField

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models.base import ActivityPubModel
from bluebottle.activity_pub.models.actors import Actor, Organization, Person, Team
from bluebottle.activity_pub.models.events import SubEvent, Event, DoGoodActivity
from bluebottle.activity_pub.tasks import publish_to_recipient
from bluebottle.activity_pub.utils import get_platform_actor

from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.time_based.models import Registration

from bluebottle.utils.models import ChoiceItem, DjangoChoices


class AdoptionTypeChoices(DjangoChoices):
    clone = ChoiceItem(
        'clone',
        _('Use received activities as template to create your own activities.')
    )
    link = ChoiceItem(
        'link',
        _('Show adopted activities as links to the partner platform.')
    )
    sync = ChoiceItem(
        'sync',
        _('Fully synced copy; Participants sync with source.')
    )


class ShortAdoptionTypeChoices(DjangoChoices):
    clone = ChoiceItem(
        'clone',
        _('Template')
    )
    link = ChoiceItem(
        'link',
        _('Link')
    )
    sync = ChoiceItem(
        'sync',
        _('Fully synced')
    )


class PublishModeChoices(DjangoChoices):
    manual = ChoiceItem(
        'manual',
        _('Choose which activities you want to share')
    )
    automatic = ChoiceItem(
        'automatic',
        _('Activities will be shared when they go live.')
    )


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')

    default_recipients = []

    def save(self, *args, **kwargs):
        if not getattr(self, 'actor_id', None):
            self.actor = get_platform_actor()

        created = not self.pk

        super().save(*args, **kwargs)

        if created and self.is_local:
            for recipient in self.default_recipients:
                Recipient.objects.create(
                    actor=recipient,
                    activity=self
                )


class Recipient(models.Model):
    activity = models.ForeignKey('activity_pub.Activity', on_delete=models.CASCADE, related_name='recipients')
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='recipients')
    send = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.models.transitions import Start, Finish, Cancel

        created = not self.pk
        super().save(*args, **kwargs)

        if created and not self.actor.is_local:
            publish_to_recipient.delay_on_commit(self, connection.tenant)

            if isinstance(self.activity, Create):
                for transition_cls in [Start, Finish, Cancel]:
                    for transition in transition_cls.objects.filter(
                        object=self.activity.object
                    ):
                        Recipient.objects.get_or_create(
                            actor=self.actor,
                            activity=transition
                        )

    def publish(self):
        adapter.publish(self.activity, self.actor)

        self.send = True
        self.save()

    class Meta:
        verbose_name = _("Recipient")
        verbose_name_plural = _("Recipients")
        unique_together = ('activity', 'actor')


class Follow(Activity):
    object = models.ForeignKey(
        'activity_pub.Actor',
        verbose_name=_("Partner"),
        on_delete=models.CASCADE
    )

    default_owner = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        verbose_name=_("Default activity owner"),
        help_text=_(
            "This user will be assigned as the activity manager for any activity "
            "cloned from a template. It can be left empty and no activity manager "
            "will be assigned by default."
        ),
        on_delete=models.SET_NULL,
    )

    automatic_adoption_activity_types = MultiSelectField(
        verbose_name=_("Automatically adopted these activity types"),
        max_length=300,
        choices=InitiativePlatformSettings.ACTIVITY_TYPES,
        null=True,
        blank=True,
        help_text=_("Selected activity types are automatically adopted when they are published."),
    )

    adoption_type = models.CharField(
        choices=AdoptionTypeChoices.choices,
        default=AdoptionTypeChoices.clone,
        verbose_name=_("Adoption type"),
        help_text=_("Select how a received activity should be adopted."),
    )

    publish_mode = models.CharField(
        choices=PublishModeChoices.choices,
        default=PublishModeChoices.manual,
        verbose_name=_("Publish mode"),
    )

    def follow(self, url, **kwargs):
        self.object = adapter.discover(url)

    @property
    def default_recipients(self):
        yield self.object

    @property
    def shared_activities(self):
        if self.is_local:
            return Event.objects.filter(
                create__actor=self.object,
            )
        return Recipient.objects.filter(
            actor=self.actor,
            activity__create__isnull=False,
            send=True
        )

    @property
    def short_adoption_type(self):
        # `adoption_type` is stored on Follow and may contain legacy/unknown values.
        # The admin should never 500 because of an unexpected choice value.
        return ShortAdoptionTypeChoices.labels.get(
            self.adoption_type,
            str(self.adoption_type) if self.adoption_type is not None else ''
        )

    @property
    def adopted_activities(self):
        if self.is_local:
            return Event.objects.filter(
                create__actor=self.object,
            ).filter(
                models.Q(link__isnull=False) | models.Q(adopted__isnull=False)
            )
        return Accept.objects.filter(
            actor=self.actor,
        )

    @property
    def unpublished_activities(self):
        return DoGoodActivity.objects.filter(
            status__in=['open', 'succeeded', 'full', 'partially_funded', 'running'],
        ).exclude(
            activity_pub_model__create__recipients__actor=self.actor,
        )

    @property
    def unpublished_open_activities(self):
        return self.unpublished_activities.filter(
            status__in=['open', 'full', 'running'],
        )

    @property
    def unpublished_succeeded_activities(self):
        return self.unpublished_activities.filter(
            status__in=['succeeded', 'partially_funded'],
        )

    def save(self, *args, **kwargs):
        created = not bool(self.pk)

        if not hasattr(self, 'actor'):
            self.actor = get_platform_actor()

        super().save(*args, **kwargs)

        if not created:
            Update.objects.create(
                object=self
            )

    def __str__(self):
        return str(self.object)

    class Meta:
        verbose_name = _('Connection')
        verbose_name_plural = _('Connections')


class Follower(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Consumer')
        verbose_name_plural = _('Consumers')


class Following(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')

    def __str__(self):
        try:
            return str(self.object)
        except Actor.DoesNotExist:
            return "-"


class Accept(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        from bluebottle.activity_pub.models.joins import Join

        if isinstance(self.object, Follow):
            yield self.object.actor
        elif isinstance(self.object, Event):
            create = self.object.create_set.first()
            if create:
                yield create.actor
        elif isinstance(self.object, SubEvent):
            parent = self.object.parent
            create = parent.create_set.first() if parent else None
            if create:
                yield create.actor
        elif isinstance(self.object, Join) and self.object.platform:
            yield self.object.platform

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.models.joins import Join

        created = not self.pk
        super().save(*args, **kwargs)

        if created and not self.is_local and isinstance(self.object, Join):
            registration = Registration.objects.get(
                user=self.object.actor.origin, activity=self.object.object.adopted
            )
            try:
                registration.states.accept(save=True)
            except TransitionNotPossible:
                pass


class Reject(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        from bluebottle.activity_pub.models.joins import Join

        if isinstance(self.object, Join) and self.object.platform:
            yield self.object.platform
        elif isinstance(self.object, Event):
            create = self.object.create_set.first()
            if create:
                yield create.actor
        elif isinstance(self.object, SubEvent):
            parent = self.object.parent
            create = parent.create_set.first() if parent else None
            if create:
                yield create.actor

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.models.joins import Join

        created = not self.pk
        super().save(*args, **kwargs)

        if not created or self.is_local:
            return

        if isinstance(self.object, Join):
            registration = Registration.objects.get(
                user=self.object.actor.origin, activity=self.object.object.adopted
            )
            registration.states.reject(save=True)
        elif isinstance(self.object, (Event, SubEvent)):
            self._unadopt()

    def _unadopt(self):
        Accept.objects.filter(actor=self.actor, object=self.object).delete()


class Create(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.models.transitions import Start, Finish, Cancel
        created = not self.pk
        super().save(*args, **kwargs)

        if created and self.is_local:
            if self.object.origin:
                if self.object.origin.status in ('open', 'granted', ):
                    Start.objects.create(object=self.object)
                elif self.object.origin.status == 'succeeded':
                    Finish.objects.create(object=self.object)
                elif self.object.origin.status in ('cancelled', 'rejected', 'deleted', 'expired'):
                    Cancel.objects.create(object=self.object)
        elif not self.is_local:
            follow = Follow.objects.get(object=self.actor)

            if (
                (
                    isinstance(self.object, Event) and
                    self.object.activity_type.lower() in follow.automatic_adoption_activity_types
                ) or
                isinstance(self.object, SubEvent)
            ):
                if follow.adoption_type == 'sync':
                    adapter.adopt(self.object)
                elif follow.adoption_type == 'link':
                    adapter.link(self.object)

    @property
    def followers(self):
        actor = get_platform_actor()
        followers = Follow.objects.filter(publish_mode='automatic', accept__actor=actor)
        return followers

    @property
    def default_recipients(self):
        if isinstance(self.object, SubEvent):
            return [recipient.actor for recipient in self.object.parent.create_set.get().recipients.all()]
        else:
            return [follower.actor for follower in self.followers]


class Update(Activity):
    object = models.ForeignKey(ActivityPubModel, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created and not self.object.is_local:
            if hasattr(self.object, 'adopted') and self.object.adopted:
                adapter.adopt(self.object)
            elif hasattr(self.object, 'link') and self.object.link:
                adapter.link(self.object)

    @property
    def default_recipients(self):
        from bluebottle.activity_pub.models.joins import Join

        if isinstance(self.object, Follow):
            yield self.object.object

        elif isinstance(self.object, Event):
            for create in self.object.create_set.all():
                for recipient in create.recipients.all():
                    yield recipient.actor
        elif isinstance(self.object, SubEvent):
            parent = self.object.parent
            if parent:
                for create in parent.create_set.all():
                    for recipient in create.recipients.all():
                        yield recipient.actor

        elif isinstance(self.object, Organization):
            for follow in self.object.activities.instance_of(Follow):
                yield follow.object
        elif isinstance(self.object, Person):
            recipients = set()
            for join in self.object.activities.all().instance_of(Join):
                for recipient in join.recipients.all():
                    recipients.add(recipient.actor)

            for recipient in recipients:
                yield recipient
        else:
            raise TypeError(f'Cannot create Update for {self.object}')


class Add(Activity):
    """Add a Person to a Team (team member join on the local platform)."""
    object = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='added_by',
    )
    target = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='adds',
    )
    platform = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local:
            adapter.adopt(self)

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor
            return

        event = self.target.attributed_to
        if event:
            create = event.create_set.first()
            if create and not create.actor.is_local:
                yield create.actor
