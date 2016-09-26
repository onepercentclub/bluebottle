import datetime
import pytz

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Count, Sum
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)

from bluebottle.bb_projects.models import (
    BaseProject, ProjectPhase, BaseProjectPhaseLog, BaseProjectDocument
)
from bluebottle.clients import properties
from bluebottle.bb_metrics.utils import bb_track
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.utils import StatusDefinition, PreviousStatusMixin
from bluebottle.wallposts.models import MediaWallpostPhoto, MediaWallpost, TextWallpost

from .mails import (
    mail_project_funded_internal, mail_project_complete,
    mail_project_incomplete
)
from .signals import project_funded

GROUP_PERMS = {'Staff': {'perms': ('add_project', 'change_project',
                                   'delete_project')}}


class ProjectPhaseLog(BaseProjectPhaseLog):
    pass


class ProjectManager(models.Manager):
    def search(self, query):
        qs = super(ProjectManager, self).get_queryset()

        # Apply filters
        status = query.getlist(u'status[]', None)
        if status:
            qs = qs.filter(status__slug__in=status)
        else:
            status = query.get('status', None)
            if status:
                qs = qs.filter(status__slug=status)

        country = query.get('country', None)
        if country:
            qs = qs.filter(country=country)

        location = query.get('location', None)
        if location:
            qs = qs.filter(location=location)

        category = query.get('category', None)
        if category:
            qs = qs.filter(categories__slug=category)

        theme = query.get('theme', None)
        if theme:
            qs = qs.filter(theme_id=theme)

        money_needed = query.get('money_needed', None)
        if money_needed:
            qs = qs.filter(amount_needed__gt=0)

        project_type = query.get('project_type', None)
        if project_type == 'volunteering':
            qs = qs.annotate(Count('task')).filter(task__count__gt=0)
        elif project_type == 'funding':
            qs = qs.filter(amount_asked__gt=0)
        elif project_type == 'voting':
            qs = qs.filter(status__slug__in=['voting', 'voting-done'])

        text = query.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return self._ordering(query.get('ordering', None), qs, status)

    def _ordering(self, ordering, queryset, status):
        if ordering == 'amount_asked':
            queryset = queryset.order_by('status', 'amount_asked', 'id')
        elif ordering == 'deadline':
            queryset = queryset.order_by('status', 'deadline', 'id')
        elif ordering == 'amount_needed':
            queryset = queryset.order_by('status', 'amount_needed', 'id')
            queryset = queryset.filter(amount_needed__gt=0)
        elif ordering == 'newest':
            queryset = queryset.extra(
                select={'has_campaign_started': 'campaign_started is null'})
            queryset = queryset.order_by('status', 'has_campaign_started',
                                         '-campaign_started', '-created', 'id')
        elif ordering == 'popularity':
            queryset = queryset.order_by('status', '-popularity', 'id')
            if status == 5:
                queryset = queryset.filter(amount_needed__gt=0)

        elif ordering:
            queryset = queryset.order_by('status', ordering)

        return queryset


class ProjectDocument(BaseProjectDocument):
    @property
    def document_url(self):
        content_type = ContentType.objects.get_for_model(ProjectDocument).id
        # pk may be unset if not saved yet, in which case no url can be
        # generated.
        if self.pk is not None:
            return reverse('document_download_detail',
                           kwargs={'content_type': content_type,
                                   'pk': self.pk or 1})
        return None


class Project(BaseProject, PreviousStatusMixin):
    latitude = models.DecimalField(
        _('latitude'), max_digits=21, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(
        _('longitude'), max_digits=21, decimal_places=18, null=True, blank=True)

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
        _("story"), help_text=_("This is the help text for the story field"),
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
    campaign_funded = models.DateTimeField(_('Campaign Funded'), null=True,
                                           blank=True)

    voting_deadline = models.DateTimeField(_('Voting Deadline'), null=True,
                                           blank=True)

    categories = models.ManyToManyField('categories.Category', blank=True)

    objects = ProjectManager()

    def __unicode__(self):
        if self.title:
            return self.title
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

        # Loop over all projects that where changed, or where a donation was recently done
        for project in self.objects.filter(
                Q(updated__gte=last_month) |
                Q(donation__created__gte=last_month,
                  donation__order__status__in=[StatusDefinition.SUCCESS, StatusDefinition.PENDING]) |
                Q(task__members__created__gte=last_month) |
                Q(vote__created__gte=last_month)).distinct():

            project.popularity = (
                weight * len(donations.filter(project=project)) +
                weight * len(task_members.filter(task__project=project)) +
                len(votes.filter(project=project))
            )
            project.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = self.__class__.objects

            while qs.filter(slug=original_slug).exists():
                original_slug = '{0}-{1}'.format(original_slug, counter)
                counter += 1
            self.slug = original_slug

        if not self.status:
            self.status = ProjectPhase.objects.get(slug="plan-new")

        # If the project status is moved to New or Needs Work, clear the
        # date_submitted field
        if self.status.slug in ["plan-new", "plan-needs-work"]:
            self.date_submitted = None

        # Set the submitted date
        if self.status == ProjectPhase.objects.get(
                slug="plan-submitted") and not self.date_submitted:
            self.date_submitted = timezone.now()

        # Set the campaign started date
        if self.status == ProjectPhase.objects.get(
                slug="campaign") and not self.campaign_started:
            self.campaign_started = timezone.now()

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

        if self.amount_asked:
            self.update_amounts(False)

        # FIXME: CLean up this code, make it readable
        # Project is not ended, complete, funded or stopped and its deadline has expired.
        if not self.campaign_ended and self.deadline < timezone.now() \
                and self.status.slug not in ["done-complete",
                                             "done-incomplete",
                                             "closed",
                                             "voting-done"]:
            if self.amount_asked > 0 and self.amount_donated <= 20 \
                    or not self.campaign_started:
                self.status = ProjectPhase.objects.get(slug="closed")
            elif self.amount_asked > 0 \
                    and self.amount_donated >= self.amount_asked:
                self.status = ProjectPhase.objects.get(slug="done-complete")
            else:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
            self.campaign_ended = self.deadline

        if self.status.slug in ["done-complete", "done-incomplete", "closed"] \
                and not self.campaign_ended:
            self.campaign_ended = timezone.now()

        previous_status = None
        if self.pk:
            previous_status = self.__class__.objects.get(pk=self.pk).status
        super(Project, self).save(*args, **kwargs)

        # Only log project phase if the status has changed
        if self is not None and previous_status != self.status:
            ProjectPhaseLog.objects.create(
                project=self, status=self.status)

    def update_status_after_donation(self, save=True):
        if not self.campaign_funded and not self.campaign_ended and \
                self.status not in ProjectPhase.objects.filter(
                    Q(slug="done-complete") |
                    Q(slug="done-incomplete")) and self.amount_needed <= 0:
            self.campaign_funded = timezone.now()
            if save:
                self.save()

    def update_amounts(self, save=True):
        """ Update amount based on paid and pending donations. """

        self.amount_donated = self.get_money_total(
            [StatusDefinition.PENDING, StatusDefinition.SUCCESS,
             StatusDefinition.PLEDGED])
        self.amount_needed = self.amount_asked - self.amount_donated

        if self.amount_needed < 0:
            # Should never be less than zero
            self.amount_needed = 0

        self.update_status_after_donation(False)

        if save:
            self.save()

    def get_money_total(self, status_in=None):
        """
        Calculate the total (realtime) amount of money for donations,
        optionally filtered by status.
        """

        if self.amount_asked == 0:
            # No money asked, return 0
            return 0

        donations = self.donation_set.all()

        if status_in:
            donations = donations.filter(order__status__in=status_in)

        total = donations.aggregate(sum=Sum('amount'))

        if not total['sum']:
            # No donations, manually set amount
            return 0

        return total['sum']

    @property
    def is_realised(self):
        return self.status in ProjectPhase.objects.filter(
            slug__in=['done-complete', 'done-incomplete', 'realised']).all()

    @property
    def is_funding(self):
        return self.amount_asked > 0

    def supporter_count(self, with_guests=True):
        # TODO: Replace this with a proper Supporters API
        # something like /projects/<slug>/donations
        donations = self.donation_set
        donations = donations.filter(
            order__status__in=[StatusDefinition.PLEDGED,
                               StatusDefinition.PENDING,
                               StatusDefinition.SUCCESS])
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
        return len(
            self.task_set.filter(status=Task.TaskStatuses.open).all())

    @property
    def realized_task_count(self):
        return len(
            self.task_set.filter(status=Task.TaskStatuses.realized).all())

    @property
    def from_suggestion(self):
        return len(self.suggestions.all()) > 0

    @property
    def get_open_tasks(self):
        return self.task_set.filter(status=Task.TaskStatuses.open).all()

    @property
    def date_funded(self):
        return self.campaign_funded

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
    def donated_percentage(self):
        if not self.amount_asked:
            return 0
        elif self.amount_donated > self.amount_asked:
            return 100
        return int(100 * self.amount_donated / self.amount_asked)

    @property
    def wallpost_photos(self):
        project_type = ContentType.objects.get_for_model(self)
        return MediaWallpostPhoto.objects.order_by('-mediawallpost__created').\
            filter(mediawallpost__object_id=self.id, mediawallpost__content_type=project_type)

    @property
    def wallpost_videos(self):
        project_type = ContentType.objects.get_for_model(self)
        return MediaWallpost.objects.order_by('-created').\
            filter(object_id=self.id, content_type=project_type, video_url__gt="")

    @property
    def donors(self, limit=20):
        return self.donation_set.\
            filter(order__status__in=[StatusDefinition.PLEDGED,
                                      StatusDefinition.PENDING,
                                      StatusDefinition.SUCCESS],
                   anonymous=False).\
            filter(order__user__isnull=False).\
            order_by('order__user', '-created').distinct('order__user')[:limit]

    @property
    def task_members(self, limit=20):
        return TaskMember.objects.\
            filter(task__project=self, status__in=['accepted', 'realized']).\
            order_by('member', '-created').distinct('member')[:limit]

    @property
    def posters(self, limit=20):
        return TextWallpost.objects.\
            filter(object_id=self.id).\
            order_by('author', '-created').distinct('author')[:limit]

    def get_absolute_url(self):
        """ Get the URL for the current project. """
        return 'https://{}/projects/{}'.format(properties.tenant.domain_url, self.slug)

    def get_meta_title(self, **kwargs):
        return u"%(name_project)s | %(theme)s | %(country)s" % {
            'name_project': self.title,
            'theme': self.theme.name if self.theme else '',
            'country': self.country.name if self.country else '',
        }

    def get_fb_title(self, **kwargs):
        title = _(u"{name_project} in {country}").format(
            name_project=self.title,
            country=self.country.name if self.country else '',
        )
        return title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(lang_code,
                                                      settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_fb_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u"{title} {{URL}}").format(
            title=title, twitter_handle=twitter_handle
        )

        return tweet

    class Meta(BaseProject.Meta):
        ordering = ['title']

    class Analytics:
        type = 'project'
        tags = {
            'sub_type': 'project_type',
            'status': 'status.name',
            'status_slug': 'status.slug',
            'theme': 'theme.name',
            'theme_slug': 'theme.slug',
            'location': 'location.name',
            'country': 'country_name'
        }

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
            "old_status": old_status.name,
            "new_status": new_status.name
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

    def deadline_reached(self):
        # BB-3616 "Funding projects should not look at (in)complete tasks for their status."
        if self.is_funding:
            if self.amount_donated >= self.amount_asked:
                self.status = ProjectPhase.objects.get(slug="done-complete")
            elif self.amount_donated <= 20 or not self.campaign_started:
                self.status = ProjectPhase.objects.get(slug="closed")
            else:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
        else:
            if self.task_set.filter(
                    status__in=[Task.TaskStatuses.in_progress,
                                Task.TaskStatuses.open]).count() > 0:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
            else:
                self.status = ProjectPhase.objects.get(slug="done-complete")
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
    currency = models.CharField(max_length=3, default='EUR')
    amount = models.PositiveIntegerField(_('amount (in cents)'))

    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    class Meta:
        verbose_name = _('budget line')
        verbose_name_plural = _('budget lines')

    def __unicode__(self):
        return u'{0} - {1}'.format(self.description, self.amount / 100.0)


@receiver(project_funded, weak=False, sender=Project,
          dispatch_uid="email-project-team-project-funded")
def email_project_team_project_funded(sender, instance, first_time_funded,
                                      **kwargs):
    mail_project_funded_internal(instance)


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
