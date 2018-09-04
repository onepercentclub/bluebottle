import datetime
import logging

import pytz
from adminsortable.models import SortableMixin

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Count, Sum
from django.db.models.signals import post_init, post_save, pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField

from django_summernote.models import AbstractAttachment

from moneyed.classes import Money
from polymorphic.models import PolymorphicModel
from multiselectfield import MultiSelectField

from bluebottle.analytics.tasks import queue_analytics_record
from bluebottle.bb_metrics.utils import bb_track
from bluebottle.bb_projects.models import (
    BaseProject, ProjectPhase, BaseProjectDocument
)
from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField, get_currency_choices, get_default_currency
from bluebottle.utils.managers import UpdateSignalsQuerySet
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.utils import StatusDefinition, PreviousStatusMixin, reverse_signed
from bluebottle.wallposts.models import (
    Wallpost, MediaWallpostPhoto, MediaWallpost, TextWallpost
)
from .mails import mail_project_complete, mail_project_incomplete
from .signals import project_funded  # NOQA

logger = logging.getLogger(__name__)


class ProjectLocation(models.Model):
    project = models.OneToOneField('projects.Project', primary_key=True)
    place = models.CharField(_('place'), max_length=80, null=True, blank=True)
    street = models.TextField(_('street'), max_length=80, null=True, blank=True)
    neighborhood = models.TextField(_('neighborhood'), max_length=80, null=True, blank=True)
    city = models.TextField(_('city'), max_length=80, null=True, blank=True)
    postal_code = models.CharField(_('postal_code'), max_length=20, null=True, blank=True)
    country = models.CharField(_('country'), max_length=40, null=True, blank=True)
    latitude = models.DecimalField(
        _('latitude'), max_digits=21, decimal_places=18, null=True, blank=True
    )
    longitude = models.DecimalField(
        _('longitude'), max_digits=21, decimal_places=18, null=True, blank=True
    )

    class Meta:
        verbose_name = _('Map')
        verbose_name_plural = _('Map')


class ProjectPhaseLog(models.Model):
    project = models.ForeignKey('projects.Project')
    status = models.ForeignKey('bb_projects.ProjectPhase')
    start = CreationDateTimeField(
        _('created'), help_text=_('When this project entered in this status.')
    )

    class Meta:
        verbose_name = _('project phase log')
        verbose_name_plural = _('project phase logs')

    class Analytics:
        type = 'project'
        tags = {
            'id': 'project.id',
            'sub_type': 'project.project_type',
            'status': 'status.name',
            'status_slug': 'status.slug',
            'theme': {
                'project.theme.name': {'translate': True}
            },
            'theme_slug': 'project.theme.slug',
            'location': 'project.location.name',
            'location_group': 'project.location.group.name',
            'country': 'project.country_name'
        }
        fields = {
            'id': 'project.id',
            'user_id': 'project.owner.id'
        }

        @staticmethod
        def timestamp(obj, created):
            return obj.start


class ProjectDocument(BaseProjectDocument):
    @property
    def document_url(self):
        # pk may be unset if not saved yet, in which case no url can be
        # generated.
        if self.pk is not None and self.file:
            return reverse_signed('project-document-file', args=(self.pk, ))
        return None

    @property
    def owner(self):
        return self.project.owner

    @property
    def parent(self):
        return self.project


class Project(BaseProject, PreviousStatusMixin):
    reach = models.PositiveIntegerField(
        _('Reach'), help_text=_('How many people do you expect to reach?'),
        blank=True, null=True)

    video_url = models.URLField(
        _('video'), max_length=100, blank=True, null=True, default='',
        help_text=_("Do you have a video pitch or a short movie that "
                    "explains your project? Cool! We can't wait to see it! "
                    "You can paste the link to YouTube or Vimeo video here"))

    popularity = models.FloatField(null=False, default=0)
    is_campaign = models.BooleanField(verbose_name='On homepage', default=False, help_text=_(
        "Project is part of a campaign and gets special promotion."))

    skip_monthly = models.BooleanField(_("Skip monthly"),
                                       help_text=_(
                                           "Skip this project when running monthly donations"),
                                       default=False)

    allow_overfunding = models.BooleanField(default=True)
    story = models.TextField(
        _("story"), help_text=_("Describe the project in detail"),
        blank=True, null=True)

    # TODO: Remove these fields?
    effects = models.TextField(
        _("effects"), blank=True, null=True,
        help_text=_("What will be the Impact? How will your "
                    "Smart Idea change the lives of people?"))
    for_who = models.TextField(
        _("for who"), blank=True, null=True,
        help_text=_("Describe your target group"))
    future = models.TextField(
        _("future"), blank=True, null=True,
        help_text=_("How will this project be self-sufficient and "
                    "sustainable in the long term?"))

    date_submitted = models.DateTimeField(_('Campaign Submitted'), null=True,
                                          blank=True)
    campaign_started = models.DateTimeField(_('Campaign Started'), null=True,
                                            blank=True)
    campaign_ended = models.DateTimeField(_('Campaign Ended'), null=True,
                                          blank=True)
    campaign_edited = models.DateTimeField(_('Campaign edited'), null=True,
                                           blank=True)
    campaign_funded = models.DateTimeField(_('Campaign Funded'), null=True,
                                           blank=True)
    campaign_paid_out = models.DateTimeField(_('Campaign Paid Out'), null=True,
                                             blank=True)
    voting_deadline = models.DateTimeField(_('Voting Deadline'), null=True,
                                           blank=True)

    categories = models.ManyToManyField('categories.Category', blank=True)

    currencies = MultiSelectField(
        max_length=100, default=[],
        choices=lazy(get_currency_choices, tuple)()
    )

    celebrate_results = models.BooleanField(
        _('Celebrate Results'),
        help_text=_('Show celebration when project is complete'),
        default=True
    )

    PAYOUT_STATUS_CHOICES = (
        (StatusDefinition.NEEDS_APPROVAL, _('Needs approval')),
        (StatusDefinition.APPROVED, _('Approved')),
        (StatusDefinition.SCHEDULED, _('Scheduled')),
        (StatusDefinition.RE_SCHEDULED, _('Re-scheduled')),
        (StatusDefinition.IN_PROGRESS, _('In progress')),
        (StatusDefinition.PARTIAL, _('Partially paid')),
        (StatusDefinition.SUCCESS, _('Success')),
        (StatusDefinition.FAILED, _('Failed'))
    )

    payout_status = models.CharField(_('payout_status'), max_length=50, null=True, blank=True,
                                     choices=PAYOUT_STATUS_CHOICES)
    wallposts = GenericRelation(Wallpost, related_query_name='project_wallposts')
    objects = UpdateSignalsQuerySet.as_manager()

    bank_details_reviewed = models.BooleanField(
        _('Bank details reviewed'),
        help_text=_(
            'Review the project documents before marking the bank details as reviewed.'
            'After setting this project to running, the project documents will be deleted.'
            'Also, make sure to remove the documents from your device after downloading them.'
        ),
        default=False
    )

    def __unicode__(self):
        if self.title:
            return u'{}'.format(self.title)
        return self.slug

    @classmethod
    def update_popularity(self):
        """
        Update popularity score for all projects

        Popularity is calculated by the number of new donations, task members and votes
        in the last 30 days.

        Donations and task members have a weight 5 times that fo a vote.
        """
        from bluebottle.donations.models import Donation
        from bluebottle.tasks.models import TaskMember
        from bluebottle.votes.models import Vote

        weight = 5

        last_month = timezone.now() - timezone.timedelta(days=30)
        donations = Donation.objects.filter(
            order__status__in=[
                StatusDefinition.PLEDGED,
                StatusDefinition.PENDING,
                StatusDefinition.SUCCESS
            ],
            created__gte=last_month
        ).exclude(order__order_type='recurring')

        task_members = TaskMember.objects.filter(
            created__gte=last_month
        )

        votes = Vote.objects.filter(
            created__gte=last_month
        )

        # Loop over all projects that have popularity set, where a donation was recently done,
        # where a taskmember was created or that recieved a vote
        # These queries CAN be combined into one query, but that is very inefficient.
        queries = [
            Q(popularity__gt=0),
            Q(donation__created__gte=last_month,
              donation__order__status__in=[StatusDefinition.SUCCESS, StatusDefinition.PENDING]),
            Q(task__members__created__gte=last_month),
            Q(vote__created__gte=last_month)
        ]

        for query in queries:
            for project in self.objects.filter(query).distinct():
                popularity = (
                    weight * len(donations.filter(project=project)) +
                    weight * len(task_members.filter(task__project=project)) +
                    len(votes.filter(project=project))
                )
                # Save the new value to the db, but skip .save
                # this way we will not trigger signals and hit the save method
                self.objects.filter(pk=project.pk).update(popularity=popularity)

    @classmethod
    def update_status_stats(cls, tenant):
        logger.info('Updating Project Status Stats: {}'.format(tenant.name))
        timestamp = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        for status in ProjectPhase.objects.all():
            # TODO: Should we count statuses only where the project phase status is active?
            count = Project.objects.filter(status=status).count()
            logger.info('status: {}, count: {}'.format(status.name, count))
            tags = {
                'type': 'project_status_daily',
                'status': status.name,
                'status_slug': status.slug,
                'tenant': tenant.client_name,
            }
            fields = {
                'total': count,
            }
            if getattr(properties, 'CELERY_RESULT_BACKEND', None):
                queue_analytics_record.delay(timestamp=timestamp, tags=tags, fields=fields)
            else:
                queue_analytics_record(timestamp=timestamp, tags=tags, fields=fields)

    def save(self, *args, **kwargs):
        # Set valid slug
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = self.__class__.objects

            while qs.filter(slug=original_slug).exists():
                original_slug = '{0}-{1}'.format(original_slug, counter)
                counter += 1
            self.slug = original_slug

        # set default project_type if not already defined
        if not self.project_type:
            with LocalTenant():
                try:
                    self.project_type = properties.PROJECT_CREATE_TYPES[0]
                except (AttributeError, KeyError):
                    logger.warning('Tenant has no PROJECT_CREATE_TYPES: %s', properties.tenant.name,
                                   exc_info=1)

        if not self.status:
            self.status = ProjectPhase.objects.get(slug="plan-new")

        if not self.currencies and self.amount_asked:
            self.currencies = [str(self.amount_asked.currency)]

        # Set a default deadline of 30 days
        if not self.deadline:
            self.deadline = timezone.now() + datetime.timedelta(days=30)

        # make sure the deadline is set to the end of the day, amsterdam time
        tz = pytz.timezone('Europe/Amsterdam')
        local_time = self.deadline.astimezone(tz)
        if local_time.time() != datetime.time(23, 59, 59):
            self.deadline = tz.localize(
                datetime.datetime.combine(local_time.date(),
                                          datetime.time(23, 59, 59))
            )

        if not self.amount_asked:
            self.amount_asked = Money(0, get_default_currency())

        if self.amount_asked.amount:
            self.update_amounts(False)

        if self.amount_asked and self.amount_asked.currency != self.amount_extra.currency:
            self.amount_extra = Money(
                self.amount_extra.amount, self.amount_asked.currency
            )

        # Project is not ended, complete, funded or stopped and its deadline has expired.
        if not self.campaign_ended and self.deadline < timezone.now() \
                and self.status.slug not in ["done-complete",
                                             "done-incomplete",
                                             "closed",
                                             "voting-done"]:
            self.update_status_after_deadline()
            self.campaign_ended = self.deadline

        if self.payout_status == 'success' and not self.campaign_paid_out:
            self.campaign_paid_out = now()

        if self.payout_status == 're_scheduled' and self.campaign_paid_out:
            self.campaign_paid_out = None

        self.update_payout_approval()

        if not self.task_manager:
            self.task_manager = self.owner

        if self.status.slug not in (
            'plan-new', 'plan-submitted', 'plan-needs-work',
        ):
            for document in self.documents.all():
                document.delete()

        # Set all task.author to project.task_manager
        self.task_set.exclude(author=self.task_manager).update(author=self.task_manager)

        super(Project, self).save(*args, **kwargs)

        # Set a default deadline of 30 days
        try:
            self.projectlocation
        except ProjectLocation.DoesNotExist:
            ProjectLocation.objects.create(project=self)

    def update_status_after_donation(self, save=True):
        if not self.campaign_funded and not self.campaign_ended and \
                self.status.slug not in ["done-complete", "done-incomplete"] and \
                self.amount_needed.amount <= 0:
            self.campaign_funded = timezone.now()
            if save:
                self.save()

    def update_amounts(self, save=True):
        """
        Update amount based on paid and pending donations.
        """
        total = self.get_money_total([StatusDefinition.PENDING,
                                      StatusDefinition.SUCCESS,
                                      StatusDefinition.PLEDGED])

        self.amount_donated = total
        self.amount_needed = self.amount_asked - self.amount_donated

        self.update_status_after_donation(False)

        if save:
            self.save()

    def get_money_total(self, status_in=None):
        """
        Calculate the total (realtime) amount of money for donations,
        optionally filtered by status.
        """
        if not self.amount_asked:
            # No money asked, return 0
            return Money(0, 'EUR')

        donations = self.donation_set

        if status_in:
            donations = donations.filter(order__status__in=status_in)

        totals = donations.values('amount_currency').annotate(total=Sum('amount'))
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]

        amounts = [convert(amount, self.amount_asked.currency) for amount in amounts]

        return sum(amounts) or Money(0, self.amount_asked.currency)

    @property
    def donations(self):
        success = [StatusDefinition.PENDING, StatusDefinition.SUCCESS, StatusDefinition.PLEDGED]
        return self.donation_set.filter(order__status__in=success)

    @property
    def totals_donated(self):
        confirmed = [StatusDefinition.PENDING, StatusDefinition.SUCCESS]
        donations = self.donation_set.filter(order__status__in=confirmed)
        totals = [
            Money(data['amount__sum'], data['amount_currency']) for data in
            donations.values('amount_currency').annotate(Sum('amount')).order_by()
        ]
        return totals

    @property
    def is_realised(self):
        return self.status in ProjectPhase.objects.filter(
            slug__in=['done-complete', 'done-incomplete', 'realised']).all()

    @property
    def is_funding(self):
        return self.amount_asked.amount > 0

    @property
    def has_survey(self):
        return len(self.response_set.all()) > 0

    @property
    def expertise_based(self):
        return any(task.skill.expertise for task in self.task_set.all() if task.skill)

    def supporter_count(self, with_guests=True):
        # TODO: Replace this with a proper Supporters API
        # something like /projects/<slug>/donations
        donations = self.donation_set
        donations = donations.filter(
            order__status__in=[
                StatusDefinition.PLEDGED,
                StatusDefinition.PENDING,
                StatusDefinition.SUCCESS,
                StatusDefinition.CANCELLED,
                StatusDefinition.REFUND_REQUESTED,
            ]
        )

        count = donations.all().aggregate(total=Count('order__user', distinct=True))['total']

        if with_guests:
            donations = self.donation_set
            donations = donations.filter(
                order__status__in=[StatusDefinition.PLEDGED,
                                   StatusDefinition.PENDING,
                                   StatusDefinition.SUCCESS])
            donations = donations.filter(order__user__isnull=True)
            count += len(donations.all())
        return count

    @property
    def country_name(self):
        try:
            if self.country:
                return self.country.name
            elif self.location:
                return self.location.country.name
        except AttributeError:
            return ''

    @property
    def vote_count(self):
        return self.vote_set.count()

    @property
    def task_count(self):
        return self.task_set.exclude(status=Task.TaskStatuses.closed).count()

    @property
    def realized_task_count(self):
        return self.task_set.filter(status=Task.TaskStatuses.realized).count()

    @property
    def open_task_count(self):
        return self.task_set.filter(status=Task.TaskStatuses.open).count()

    @property
    def full_task_count(self):
        return self.task_set.filter(status=Task.TaskStatuses.full).count()

    @property
    def from_suggestion(self):
        return len(self.suggestions.all()) > 0

    @property
    def date_funded(self):
        return self.campaign_funded

    @property
    def donation_totals(self):
        return self.get_money_total([StatusDefinition.PENDING,
                                     StatusDefinition.SUCCESS,
                                     StatusDefinition.PLEDGED])

    @property
    def amount_pending(self):
        return self.get_money_total([StatusDefinition.PENDING])

    @property
    def amount_safe(self):
        return self.get_money_total([StatusDefinition.SUCCESS])

    @property
    def amount_pledged(self):
        return self.get_money_total([StatusDefinition.PLEDGED])

    @property
    def amount_cancelled(self):
        return self.get_money_total([
            StatusDefinition.CANCELLED,
            StatusDefinition.REFUND_REQUESTED,
            StatusDefinition.REFUNDED,
        ])

    @property
    def donated_percentage(self):
        if not self.amount_asked.amount:
            return 0
        elif self.amount_donated.amount > self.amount_asked.amount:
            return 100
        return int(100 * self.amount_donated.amount / self.amount_asked.amount)

    @property
    def wallpost_photos(self):
        project_type = ContentType.objects.get_for_model(self)
        return MediaWallpostPhoto.objects.order_by('-mediawallpost__created'). \
            filter(mediawallpost__object_id=self.id,
                   mediawallpost__content_type=project_type,
                   results_page=True)

    @property
    def wallpost_videos(self):
        project_type = ContentType.objects.get_for_model(self)
        return MediaWallpost.objects.order_by('-created'). \
            filter(object_id=self.id, content_type=project_type, video_url__gt="")

    @property
    def donors(self, limit=20):
        return self.donation_set. \
            filter(order__status__in=[StatusDefinition.PLEDGED,
                                      StatusDefinition.PENDING,
                                      StatusDefinition.SUCCESS]). \
            filter(anonymous=False). \
            filter(order__user__isnull=False). \
            order_by('order__user', 'name', '-created').distinct('order__user', 'name')[:limit]

    @property
    def task_members(self, limit=20):
        return TaskMember.objects. \
            filter(task__project=self, status__in=['accepted', 'realized']). \
            order_by('member', '-created').distinct('member')[:limit]

    @property
    def posters(self, limit=20):
        return TextWallpost.objects.filter(
            object_id=self.id,
            content_type=ContentType.objects.get_for_model(self.__class__)
        ).order_by('author', '-created').distinct('author')[:limit]

    @property
    def can_refund(self):
        return (
            properties.ENABLE_REFUNDS and
            self.amount_donated.amount > 0 and
            (not self.payout_status or self.payout_status == StatusDefinition.NEEDS_APPROVAL) and
            self.status.slug in ('done-incomplete', 'closed')
        )

    @property
    def days_left(self):
        delta = (self.deadline - now()).days
        if delta < 0:
            delta = 0
        return delta

    def get_absolute_url(self):
        """ Get the URL for the current project. """
        return 'https://{}/projects/{}'.format(properties.tenant.domain_url, self.slug)

    class Meta(BaseProject.Meta):
        permissions = (
            ('approve_payout', 'Can approve payouts for projects'),
            ('export_supporters', 'Can export supporters for projects'),
            ('api_read_project', 'Can view projects through the API'),
            ('api_add_project', 'Can add projects through the API'),
            ('api_change_project', 'Can change projects through the API'),
            ('api_delete_project', 'Can delete projects through the API'),

            ('api_read_own_project', 'Can view own projects through the API'),
            ('api_add_own_project', 'Can add own projects through the API'),
            ('api_change_own_project', 'Can change own projects through the API'),
            ('api_change_own_running_project', 'Can change own running projects through the API'),
            ('api_delete_own_project', 'Can delete own projects through the API'),

            ('api_read_projectdocument', 'Can view project documents through the API'),
            ('api_add_projectdocument', 'Can add project documents through the API'),
            ('api_change_projectdocument', 'Can change project documents through the API'),
            ('api_delete_projectdocument', 'Can delete project documents through the API'),

            ('api_read_own_projectdocument', 'Can view project own documents through the API'),
            ('api_add_own_projectdocument', 'Can add own project documents through the API'),
            ('api_change_own_projectdocument', 'Can change own project documents through the API'),
            ('api_delete_own_projectdocument', 'Can delete own project documents through the API'),

            ('api_read_projectbudgetline', 'Can view project budget lines through the API'),
            ('api_add_projectbudgetline', 'Can add project budget lines through the API'),
            ('api_change_projectbudgetline', 'Can change project budget lines through the API'),
            ('api_delete_projectbudgetline', 'Can delete project budget lines through the API'),

            ('api_read_own_projectbudgetline', 'Can view own project budget lines through the API'),
            ('api_add_own_projectbudgetline', 'Can add own project budget lines through the API'),
            ('api_change_own_projectbudgetline', 'Can change own project budget lines through the API'),
            ('api_delete_own_projectbudgetline', 'Can delete own project budget lines through the API'),

        )
        ordering = ['title']

    def status_changed(self, old_status, new_status):
        status_complete = ProjectPhase.objects.get(slug="done-complete")
        status_incomplete = ProjectPhase.objects.get(slug="done-incomplete")

        if new_status == status_complete:
            mail_project_complete(self)
        if new_status == status_incomplete:
            mail_project_incomplete(self)

        data = {
            "Project": self.title,
            "Owner": self.owner.email,
            "old_status": old_status.slug,
            "new_status": new_status.slug
        }

        if old_status.slug in ('plan-new',
                               'plan-submitted',
                               'plan-needs-work',
                               'voting',
                               'voting-done',
                               'campaign') and new_status.slug in ('done-complete',
                                                                   'done-incomplete',
                                                                   'closed'):
            bb_track("Project Completed", data)

    def check_task_status(self):
        if (not self.is_funding and
                all([task.status == Task.TaskStatuses.realized for task in self.task_set.all()])):
            self.status = ProjectPhase.objects.get(slug='done-complete')
            self.save()

    def update_payout_approval(self):
        if self.is_funding \
                and self.status.slug in ["done-complete", "done-incomplete"] \
                and not self.payout_status:
            self.payout_status = 'needs_approval'

        # If the project is re-opened, payout-status should be cleaned
        if self.status.slug not in ["done-complete", "done-incomplete"] \
                and self.payout_status == 'needs_approval':
            self.payout_status = None

    def update_status_after_deadline(self):
        if self.status.slug == 'campaign':
            if self.is_funding:
                if self.amount_donated + self.amount_extra >= self.amount_asked:
                    self.status = ProjectPhase.objects.get(slug="done-complete")
                elif self.amount_donated.amount <= 20 or not self.campaign_started:
                    self.status = ProjectPhase.objects.get(slug="closed")
                else:
                    self.status = ProjectPhase.objects.get(slug="done-incomplete")
                self.update_payout_approval()
            else:
                if self.task_set.filter(
                        status__in=[Task.TaskStatuses.in_progress,
                                    Task.TaskStatuses.open,
                                    Task.TaskStatuses.closed]).count() > 0:
                    self.status = ProjectPhase.objects.get(slug="done-incomplete")
                else:
                    self.status = ProjectPhase.objects.get(slug="done-complete")

    def deadline_reached(self):
        # BB-3616 "Funding projects should not look at (in)complete tasks for their status."
        self.update_status_after_deadline()
        self.campaign_ended = now()
        self.save()

        data = {
            "Project": self.title,
            "Author": self.owner.username
        }

        bb_track("Project Deadline Reached", data)


class ProjectBudgetLine(models.Model):
    """
    BudgetLine: Entries to the Project Budget sheet.
    This is the budget for the amount asked from this
    website.
    """
    project = models.ForeignKey('projects.Project')
    description = models.CharField(_('description'), max_length=255, default='')
    amount = MoneyField()

    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    @property
    def owner(self):
        return self.project.owner

    @property
    def parent(self):
        return self.project

    class Meta:
        verbose_name = _('budget line')
        verbose_name_plural = _('budget lines')

    def __unicode__(self):
        return u'{0} - {1}'.format(self.description, self.amount)


class ProjectAddOn(PolymorphicModel):

    type = 'base'

    project = models.ForeignKey('projects.Project', related_name='addons')
    serializer = 'bluebottle.projects.serializers.BaseProjectAddOnSerializer'


class ProjectImage(AbstractAttachment):
    """
    Project Image: Image that is directly associated with the project.

    Can for example be used in project descriptions

    """
    project = models.ForeignKey('projects.Project')

    class Meta:
        verbose_name = _('project image')
        verbose_name_plural = _('project images')
        permissions = (
            ('api_read_projectimage', 'Can view project imagesthrough the API'),
            ('api_add_projectimage', 'Can add project images through the API'),
            ('api_change_projectimage', 'Can change project images through the API'),
            ('api_delete_projectimage', 'Can delete project images through the API'),

            ('api_read_own_projectimage', 'Can view own project images through the API'),
            ('api_add_own_projectimage', 'Can add own project images through the API'),
            ('api_change_own_projectimage', 'Can change own project images through the API'),
            ('api_delete_own_projectimage', 'Can delete own project images through the API'),
        )

    @property
    def parent(self):
        return self.project

    def save(self, project_id=None, *args, **kwargs):
        if project_id:
            self.project_id = int(project_id[0])

        super(ProjectImage, self).save(*args, **kwargs)


class ProjectSearchFilter(SortableMixin):

    FILTER_OPTIONS = (
        ('location', _('Location')),
        ('theme', _('Theme')),
        ('skills', _('Skill')),
        ('date', _('Date')),
        ('status', _('Status')),
        ('type', _('Type')),
        ('category', _('Category')),
    )

    project_settings = models.ForeignKey('projects.ProjectPlatformSettings',
                                         null=True,
                                         related_name='filters')
    name = models.CharField(max_length=100, choices=FILTER_OPTIONS)
    default = models.CharField(max_length=100, blank=True, null=True)
    values = models.CharField(max_length=500, blank=True, null=True,
                              help_text=_('Comma separated list of possible values'))
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ['sequence']


class ProjectCreateTemplate(models.Model):

    project_settings = models.ForeignKey('projects.ProjectPlatformSettings',
                                         null=True,
                                         related_name='templates')
    name = models.CharField(max_length=300)
    sub_name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)

    default_amount_asked = MoneyField(null=True, blank=True)
    default_title = models.CharField(max_length=300, null=True, blank=True,
                                     help_text=_('Default project title'))
    default_pitch = models.TextField(null=True, blank=True,
                                     help_text=_('Default project pitch'))
    default_description = models.TextField(null=True, blank=True,
                                           help_text=_('Default project description'))
    default_image = models.ImageField(null=True, blank=True,
                                      help_text=_('Default project image'))


class CustomProjectFieldSettings(SortableMixin):

    project_settings = models.ForeignKey('projects.ProjectPlatformSettings',
                                         null=True,
                                         related_name='extra_fields')

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    @property
    def slug(self):
        return slugify(self.name)

    class Meta:
        ordering = ['sequence']


class CustomProjectField(models.Model):
    project = models.ForeignKey('projects.Project', related_name='extra')
    field = models.ForeignKey('projects.CustomProjectFieldSettings')
    value = models.CharField(max_length=5000, null=True, blank=True)


class ProjectPlatformSettings(BasePlatformSettings):
    PROJECT_CREATE_OPTIONS = (
        ('sourcing', _('Sourcing')),
        ('funding', _('Funding')),
    )

    PROJECT_CONTACT_TYPE_OPTIONS = (
        ('organization', _('Organization')),
        ('personal', _('Personal')),
    )

    PROJECT_CREATE_FLOW_OPTIONS = (
        ('combined', _('Combined')),
        ('choice', _('Choice')),
    )

    PROJECT_CONTACT_OPTIONS = (
        ('mail', _('E-mail')),
        ('phone', _('Phone')),
    )

    PROJECT_SHARE_OPTIONS = (
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('facebookAtWork', _('Facebook at Work')),
        ('linkedin', _('LinkedIn')),
        ('whatsapp', _('Whatsapp')),
        ('email', _('Email')),
    )

    create_types = MultiSelectField(max_length=100, choices=PROJECT_CREATE_OPTIONS)
    contact_types = MultiSelectField(max_length=100, choices=PROJECT_CONTACT_TYPE_OPTIONS)
    share_options = MultiSelectField(
        max_length=100, choices=PROJECT_SHARE_OPTIONS, blank=True
    )
    facebook_at_work_url = models.URLField(max_length=100, null=True, blank=True)
    allow_anonymous_rewards = models.BooleanField(
        _('Allow guests to donate rewards'), default=True
    )
    create_flow = models.CharField(max_length=100, choices=PROJECT_CREATE_FLOW_OPTIONS)
    contact_method = models.CharField(max_length=100, choices=PROJECT_CONTACT_OPTIONS)

    class Meta:
        verbose_name_plural = _('project platform settings')
        verbose_name = _('project platform settings')


@receiver(post_init, sender=Project,
          dispatch_uid="bluebottle.projects.Project.post_init")
def project_post_init(sender, instance, **kwargs):
    instance._init_status = instance.status_id


@receiver(post_save, sender=Project,
          dispatch_uid="bluebottle.projects.Project.post_save")
def project_post_save(sender, instance, **kwargs):
    try:
        init_status, current_status = None, None

        try:
            init_status = ProjectPhase.objects.get(id=instance._init_status)
        except ProjectPhase.DoesNotExist:
            pass

        try:
            current_status = instance.status
        except ProjectPhase.DoesNotExist:
            pass

        if init_status != current_status:
            instance.status_changed(init_status, current_status)
    except AttributeError:
        pass


@receiver(post_save, sender=Project, dispatch_uid="updating_suggestion")
def project_submitted_update_suggestion(sender, instance, **kwargs):
    if instance.status.slug == 'plan-submitted':
        # Only one suggestion can be connected to a project
        suggestion = instance.suggestions.first()
        if suggestion and suggestion.status == 'in_progress':
            suggestion.status = 'submitted'
            suggestion.save()

    if instance.status.slug == 'plan-needs-work':
        suggestion = instance.suggestions.first()
        if suggestion and suggestion.status == 'submitted':
            suggestion.status = 'in_progress'
            suggestion.save()


@receiver(post_save, sender=Project)
def create_phaselog(sender, instance, created, **kwargs):
    # Only log project phase if the status has changed
    if instance._original_status != instance.status or created:
        ProjectPhaseLog.objects.create(
            project=instance, status=instance.status
        )


@receiver(pre_save, sender=Project, dispatch_uid="updating_suggestion")
def set_dates(sender, instance, **kwargs):
    # If the project status is moved to New or Needs Work, clear the
    # date_submitted field
    if instance.status.slug in ["plan-new", "plan-needs-work"]:
        instance.date_submitted = None

    # Set the submitted date
    if instance.status.slug == 'plan-submitted' and not instance.date_submitted:
        instance.date_submitted = timezone.now()

    # Set the campaign started date
    if instance.status.slug == 'campaign' and not instance.campaign_started:
        instance.campaign_started = timezone.now()

    if instance.status.slug in ["done-complete", "done-incomplete", "closed"] \
            and not instance.campaign_ended:
        instance.campaign_ended = timezone.now()
