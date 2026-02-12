import uuid
from builtins import object, str

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import SET_NULL
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from djchoices.choices import ChoiceItem, DjangoChoices
from future.utils import python_2_unicode_compatible
from multiselectfield import MultiSelectField
from parler.managers import TranslatableManager, TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel, PolymorphicTypeInvalid
from polymorphic.query import PolymorphicQuerySet

from bluebottle.files.fields import ImageField, PrivateDocumentField
from bluebottle.follow.models import Follow
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.offices.models import OfficeRestrictionChoices
from bluebottle.organizations.models import Organization
from bluebottle.segments.models import SegmentType, Segment
from bluebottle.utils.managers import TranslatablePolymorphicManager
from bluebottle.utils.models import ValidatedModelMixin
from bluebottle.utils.utils import get_current_host, get_current_language


@python_2_unicode_compatible
class Activity(TriggerMixin, ValidatedModelMixin, PolymorphicModel):
    class TeamActivityChoices(DjangoChoices):
        teams = ChoiceItem("teams", label=_("Teams"))
        individuals = ChoiceItem("individuals", label=_("Individuals"))

    owner = models.ForeignKey(
        "members.Member",
        verbose_name=_("activity manager"),
        related_name="activities",
        on_delete=models.CASCADE,
    )

    highlight = models.BooleanField(
        default=False, help_text=_("Highlight this activity to show it on homepage")
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=40)

    review_status = models.CharField(max_length=40, default="draft")

    initiative = models.ForeignKey(
        Initiative,
        related_name="activities",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    theme = models.ForeignKey(
        "initiatives.Theme", null=True, blank=True, on_delete=SET_NULL
    )
    categories = models.ManyToManyField("categories.Category", blank=True)

    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Partner organisation'),
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name="activities",
    )

    host_organization = models.ForeignKey(
        Organization,
        verbose_name=_('Host organisation'),
        help_text=_('The organisation that shared this activity from another platform'),
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name="hosted_activities",
    )

    office_location = models.ForeignKey(
        "geo.Location",
        verbose_name=_("Host work location"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    office_restriction = models.CharField(
        _("Restrictions"),
        default=OfficeRestrictionChoices.all,
        choices=OfficeRestrictionChoices.choices,
        blank=True,
        null=True,
        max_length=100,
    )

    has_deleted_data = models.BooleanField(
        _("Has anonymised and/or deleted data"),
        default=False,
        help_text=_(
            "Due to company policies and local laws, user data maybe deleted in this activity."
        ),
    )

    deleted_successful_contributors = models.PositiveIntegerField(
        _("Number of deleted successful contributors"), default=0, null=True, blank=True
    )

    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=100, default="new")
    description = QuillField(_("Description"), blank=True)
    team_activity = models.CharField(
        _("participation"),
        max_length=100,
        default=TeamActivityChoices.individuals,
        choices=TeamActivityChoices.choices,
        blank=True,
        help_text=_("Is this activity open for individuals or can only teams sign up?"),
    )
    image = ImageField(blank=True, null=True)

    origin = models.ForeignKey(
        'activity_pub.Event', null=True, related_name="adopted_activities", on_delete=models.SET_NULL
    )

    video_url = models.URLField(
        _("video"),
        max_length=2048,
        blank=True,
        null=True,
        default="",
        help_text=_(
            "Make your activity come alive with a video. "
            "You can paste the link to YouTube or Vimeo here."
        ),
    )

    next_step_link = models.URLField(
        _("Redirect step link"),
        max_length=2048,
        blank=True,
        null=True,
        default="",
        help_text=_(
            "This link is shown after a user joined as the next step for the activity"
        ),
    )

    next_step_title = models.CharField(
        _("Redirect step title"),
        max_length=100,
        blank=True,
        null=True,
        default="",
        help_text=_("The title in the popup after a user joined the activity"),
    )

    next_step_button_label = models.CharField(
        _("Redirect step button label"),
        max_length=100,
        blank=True,
        null=True,
        default="",
        help_text=_("The title on the next link button"),
    )

    next_step_description = models.TextField(
        _("Redirect step description"),
        blank=True,
        null=True,
        default="",
        help_text=_("A description to explain what the next step is"),
    )

    segments = models.ManyToManyField(
        "segments.segment",
        verbose_name=_("Segment"),
        related_name="activities",
        blank=True,
    )

    followers = GenericRelation("follow.Follow", object_id_field="instance_id")
    messages = GenericRelation("notifications.Message")

    follows = GenericRelation(Follow, object_id_field="instance_id")

    activity_type = _("Activity")

    auto_approve = True

    tos_accepted = models.BooleanField(
        _("Terms of Service accepted"),
        default=False,
        help_text=_("Has the user accepted the terms of service for this activity?")
    )

    @property
    def link(self):
        return None

    @property
    def event(self):
        from bluebottle.activity_pub.models import Event
        return Event.objects.get(object=self)

    @property
    def activity_pub_url(self):
        from bluebottle.activity_pub.models import Event
        try:
            return self.event.iri or self.event.pub_url
        except Event.DoesNotExist:
            return None

    @property
    def details(self):
        return f"{self.description.html}, {self.get_absolute_url()}"

    @property
    def owners(self):
        if self.owner_id:
            yield self.owner
        if self.initiative:
            yield self.initiative.owner
            for manager in self.initiative.activity_managers.all():
                yield manager

    @property
    def succeeded_contributor_count(self):
        raise NotImplementedError

    @property
    def activity_date(self):
        raise NotImplementedError

    @property
    def stats(self):
        return {}

    @property
    def required_fields(self):
        from bluebottle.initiatives.models import InitiativePlatformSettings

        fields = ['theme']
        if Location.objects.count():
            fields.append("office_location")
            if InitiativePlatformSettings.load().enable_office_regions:
                fields.append("office_restriction")
        if not self.initiative_id:
            fields.append("image")

        return fields

    @property
    def required(self):
        for field in super().required:
            yield field

        if self.pk:
            for question in self.questions.filter(required=True):
                try:
                    answer = self.answers.get(question=question)
                    if not answer.is_valid:
                        yield f'answers.{question.id}'

                except ActivityAnswer.DoesNotExist:
                    yield f'answers.{question.id}'

    @property
    def questions(self):
        return ActivityQuestion.objects.filter(activity_types__contains=self._meta.model_name)

    class Meta(object):
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        permissions = (
            ("api_read_activity", "Can view activity through the API"),
            ("api_read_own_activity", "Can view own activity through the API"),
            ("api_review_activity", "Can review activities through the API"),
        )

    def __str__(self):
        return self.title or str(_("-empty-"))

    def save(self, **kwargs):
        if not self.theme_id and self.initiative_id:
            self.theme = self.initiative.theme
        if self.slug in ["", "new"]:
            if self.title and slugify(self.title):
                self.slug = slugify(self.title)
            else:
                self.slug = "new"

        if not self.owner_id and self.initiative:
            self.owner = self.initiative.owner

        super(Activity, self).save(**kwargs)

        if not self.segments.count():
            for segment in self.owner.segments.filter(segment_type__inherit=True).all():
                self.segments.add(segment)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        try:
            type = self.get_real_instance().__class__.__name__.lower()
        except PolymorphicTypeInvalid:
            type = self.__class__.__name__.lower()
        return (
            f"{domain}/{language}/activities/details/{type}/{self.id}/{self.slug}"
        )

    def get_admin_url(self):
        domain = get_current_host()
        url = reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])
        return f"{domain}{url}"

    @property
    def organizer(self):
        if self.pk:
            return self.contributors.instance_of(Organizer).first()


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    # This fixing deleting related polymorphic objects through admin
    if hasattr(sub_objs, "non_polymorphic"):
        sub_objs = sub_objs.non_polymorphic()
    return models.CASCADE(collector, field, sub_objs, using)


@python_2_unicode_compatible
class Contributor(TriggerMixin, PolymorphicModel):
    status = models.CharField(max_length=40)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    contributor_date = models.DateTimeField(null=True, blank=True)

    activity = models.ForeignKey(
        Activity, related_name="contributors", on_delete=NON_POLYMORPHIC_CASCADE
    )

    team = models.ForeignKey(
        "activities.Team",
        verbose_name=_("Old team"),
        null=True,
        blank=True,
        related_name="members",
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(
        "members.Member",
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def contributor(self):
        return self

    @property
    def status_label(self):
        if self.states.current_state:
            return self.states.current_state.name

    @property
    def owner(self):
        return self.user

    @property
    def is_team_captain(self):
        return self.team and self.user == self.team.owner

    @property
    def date(self):
        return self.activity.contributor_date

    class Meta(object):
        ordering = ("-created",)
        verbose_name = _("Contribution")
        verbose_name_plural = _("Contributions")

    @property
    def type(self):
        return self.polymorphic_ctype.model_class()._meta.verbose_name

    def __str__(self):
        if self.user:
            return str(self.user)
        return str(_("Anonymous"))


@python_2_unicode_compatible
class Organizer(Contributor):
    class Meta(object):
        verbose_name = _("Activity owner")
        verbose_name_plural = _("Activity owners")

    class JSONAPIMeta(object):
        resource_name = "contributors/organizers"


class Contribution(TriggerMixin, PolymorphicModel):
    status = models.CharField(max_length=40)

    created = models.DateTimeField(default=timezone.now)
    start = models.DateTimeField(_("start"), null=True, blank=True)
    end = models.DateTimeField(_("end"), null=True, blank=True)

    contributor = models.ForeignKey(
        Contributor,
        related_name="contributions",
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def owner(self):
        return self.contributor.user

    class Meta(object):
        ordering = ("-created",)
        verbose_name = _("Contribution amount")
        verbose_name_plural = _("Contribution amounts")

    def __str__(self):
        return str(_("Contribution amount"))


class EffortContribution(Contribution):
    class ContributionTypeChoices(DjangoChoices):
        organizer = ChoiceItem("organizer", label=_("Activity Organizer"))
        deed = ChoiceItem("deed", label=_("Deed participant"))

    contribution_type = models.CharField(
        _("Contribution type"),
        max_length=20,
        choices=ContributionTypeChoices.choices,
    )

    class Meta(object):
        verbose_name = _("Effort")
        verbose_name_plural = _("Contributions")


class Invite(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    class JSONAPIMeta(object):
        resource_name = "activities/invites"


class Team(TriggerMixin, models.Model):
    status = models.CharField(max_length=40)

    activity = models.ForeignKey(
        Activity, related_name="old_teams", on_delete=NON_POLYMORPHIC_CASCADE
    )

    created = models.DateTimeField(default=timezone.now)

    owner = models.ForeignKey(
        "members.Member", related_name="teams", null=True, on_delete=models.SET_NULL
    )

    @property
    def accepted_participants(self):
        return self.members.filter(status="accepted")

    @property
    def accepted_participants_count(self):
        return len(self.accepted_participants)

    class Meta(object):
        ordering = ("-created",)
        verbose_name = _("Team")

        permissions = (
            ("api_read_team", "Can view team through the API"),
            ("api_change_team", "Can change team through the API"),
            ("api_change_own_team", "Can change own team through the API"),
        )

    @property
    def name(self):
        return _("Team {name}").format(
            name=self.owner.full_name if self.owner_id else _("Anonymous")
        )

    def __str__(self):
        return self.name


class TranslatedPolymorphicQueryset(TranslatableQuerySet, PolymorphicQuerySet):
    pass


class TranslatedPolymorphicManager(PolymorphicManager, TranslatableManager):
    queryset_class = TranslatablePolymorphicManager


class ActivityQuestion(PolymorphicModel, TranslatableModel):
    objects = TranslatablePolymorphicManager()

    VISIBILITY_CHOICES = (
        ('all', _("Everyone")),
        ('managers', _("Managers")),
    )

    class VisibilityChoices(DjangoChoices):

        all = ChoiceItem('all', label=_("Everyone"))
        managers = ChoiceItem('managers', label=_("Managers"))

    translations = TranslatedFields(
        name=models.CharField(
            _('Label'),
            help_text=_(
                'The label for this question. This is used for validation messages e.g. "[label] is required".'
            ),
            max_length=255
        ),
        question=models.CharField(max_length=255),
        help_text=models.TextField(null=True, blank=True)
    )

    activity_types = MultiSelectField(
        max_length=300,
        choices=InitiativePlatformSettings.ACTIVITY_TYPES,
        default=[choice[0] for choice in InitiativePlatformSettings.ACTIVITY_TYPES]
    )

    required = models.BooleanField(default=True)
    visibility = models.CharField(
        _('Who can see the answers?'),
        max_length=255,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.all
    )

    def __str__(self):
        return self.question

    class Meta(object):
        verbose_name = _("Form question")
        verbose_name_plural = _("Form questions")


class ActivityAnswer(PolymorphicModel):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ActivityQuestion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['activity', 'question']


class TextQuestion(ActivityQuestion, TranslatableModel):
    class JSONAPIMeta:
        resource_name = 'text-questions'


class TextAnswer(ActivityAnswer):
    answer = models.TextField()

    class JSONAPIMeta:
        resource_name = 'text-answers'

    @property
    def is_valid(self):
        return len(self.answer) > 0


class ConfirmationQuestion(ActivityQuestion, TranslatableModel):
    text = models.TextField()

    class JSONAPIMeta:
        resource_name = 'confirmation-questions'


class ConfirmationAnswer(ActivityAnswer):
    confirmed = models.BooleanField(default=False)

    class JSONAPIMeta:
        resource_name = 'confirmation-answers'

    @property
    def is_valid(self):
        return self.confirmed


class SegmentQuestion(ActivityQuestion, TranslatableModel):
    segment_type = models.ForeignKey(SegmentType, on_delete=models.CASCADE)

    class JSONAPIMeta:
        resource_name = 'segment-questions'


class SegmentAnswer(ActivityAnswer):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)

    class JSONAPIMeta:
        resource_name = 'segment-answers'

    @property
    def is_valid(self):
        return self.segment

    def save(self, *args, **kwargs):
        current_segments = self.activity.segments.filter(
            segment_type=self.question.segment_type
        ).exclude(pk=self.segment.pk)

        for segment in current_segments:
            self.activity.segments.remove(segment)

        if self.segment not in self.activity.segments.all():
            self.activity.segments.add(self.segment)

        super().save(*args, **kwargs)


class FileUploadQuestion(ActivityQuestion, TranslatableModel):
    class JSONAPIMeta:
        resource_name = 'file-upload-questions'


class FileUploadAnswer(ActivityAnswer):
    file = PrivateDocumentField(on_delete=models.CASCADE)

    class JSONAPIMeta:
        resource_name = 'file-upload-answers'

    @property
    def is_valid(self):
        return self.file


from bluebottle.activities.signals import *  # noqa
from bluebottle.activities.states import *  # noqa
