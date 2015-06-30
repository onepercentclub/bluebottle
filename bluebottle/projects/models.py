import datetime
import pytz
from django.utils.timezone import now
from bluebottle.utils.utils import StatusDefinition
from bluebottle.bb_projects.models import BaseProject, ProjectPhase, BaseProjectPhaseLog, BaseProjectDocument
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Count, Sum
from django.dispatch import receiver
from django.db.models.signals import post_init, post_save
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.conf import settings
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from bluebottle.utils.fields import ImageField
from django.template.defaultfilters import slugify
from django.utils import timezone
from .mails import mail_project_funded_internal, mail_project_complete, mail_project_incomplete
from .signals import project_funded


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_project', 'change_project', 'delete_project',
            'add_partnerorganization', 'change_partnerorganization', 'delete_partnerorganization',
        )
    }
}

class ProjectPhaseLog(BaseProjectPhaseLog):
    pass


class ProjectManager(models.Manager):

    def search(self, query):
        qs = super(ProjectManager, self).get_query_set()

        # Apply filters
        status = query.getlist(u'status[]', None)
        if status:
            qs = qs.filter(status_id__in=status)
        else:
            status = query.get('status', None)
            if status:
                qs = qs.filter(status_id=status)

        country = query.get('country', None)
        if country:
            qs = qs.filter(country=country)

        theme = query.get('theme', None)
        if theme:
            qs = qs.filter(theme_id=theme)

        text = query.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return self._ordering(query.get('ordering', None), qs, status)

    def _ordering(self, ordering, queryset, status):

        if ordering == 'amount_asked':
            queryset = queryset.order_by('amount_asked')
        elif ordering == 'deadline':
            queryset = queryset.order_by('deadline')
        elif ordering == 'amount_needed':
            queryset = queryset.order_by('amount_needed')
            queryset = queryset.filter(amount_needed__gt=0)
        elif ordering == 'newest':
            queryset = queryset.order_by('-campaign_started')
            queryset = queryset.filter(amount_needed__gt=0)
        elif ordering == 'popularity':
            queryset = queryset.order_by('-popularity')
            if status == 5:
                queryset = queryset.filter(amount_needed__gt=0)
        elif ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class ProjectDocument(BaseProjectDocument):
    pass


class Project(BaseProject):

    partner_organization = models.ForeignKey('projects.PartnerOrganization', null=True, blank=True)

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
    is_campaign = models.BooleanField(default=False, help_text=_("Project is part of a campaign and gets special promotion."))

    skip_monthly = models.BooleanField(_("Skip monthly"),
                                       help_text=_("Skip this project when running monthly donations"),
                                       default=False)

    allow_overfunding = models.BooleanField(default=True)
    story = models.TextField(_("story"), help_text=_("This is the help text for the story field"), blank=True,
                             null=True)

    # TODO: Remove these fields?
    effects = models.TextField(_("effects"), help_text=_("What will be the Impact? How will your Smart Idea change the lives of people?"), blank=True, null=True)
    for_who = models.TextField(_("for who"), help_text=_("Describe your target group"), blank=True, null=True)
    future = models.TextField(_("future"), help_text=_("How will this project be self-sufficient and sustainable in the long term?"), blank=True, null=True)

    date_submitted = models.DateTimeField(_('Campaign Submitted'), null=True, blank=True)
    campaign_started = models.DateTimeField(_('Campaign Started'), null=True, blank=True)
    campaign_ended = models.DateTimeField(_('Campaign Ended'), null=True, blank=True)
    campaign_funded = models.DateTimeField(_('Campaign Funded'), null=True, blank=True)

    objects = ProjectManager()

    def __unicode__(self):
        if self.title:
            return self.title
        return self.slug

    def update_popularity(self, save=True):
        from bluebottle.donations.models import Donation

        last_month = timezone.now() - timezone.timedelta(days=30)
        donations = Donation.objects.filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])
        donations = donations.filter(created__gte=last_month)
        donations = donations.exclude(order__order_type='recurring')

        # For all projects.
        total_recent_donors = len(donations)
        total_recent_donations = donations.aggregate(sum=Sum('amount'))['sum']

        # For this project
        donations = donations.filter(project=self)
        recent_donors = len(donations)
        recent_donations = donations.aggregate(sum=Sum('amount'))['sum']

        if recent_donors and recent_donations:
            self.popularity = 50 * (float(recent_donors) / float(total_recent_donors)) + 50 * (float(recent_donations) / float(total_recent_donations))
        else:
            self.popularity = 0
        if save:
            self.save()

    def update_status_after_donation(self):
        if not self.campaign_funded and not self.campaign_ended and \
                                            self.status not in ProjectPhase.objects.filter(Q(slug="done-complete") |
                                                           Q(slug="done-incomplete") |
                                                           Q(slug="done-stopped")) and self.amount_needed <= 0:
            self.campaign_funded = timezone.now()

            if not self.allow_overfunding:
                self.status = ProjectPhase.objects.get(slug="done-complete")
                self.campaign_ended = self.campaign_funded

            self.save()

    def update_amounts(self, save=True):
        """ Update amount based on paid and pending donations. """

        self.amount_donated = self.get_money_total([StatusDefinition.PENDING, StatusDefinition.SUCCESS])
        self.amount_needed = self.amount_asked - self.amount_donated

        if self.amount_needed < 0:
            # Should never be less than zero
            self.amount_needed = 0

        self.update_popularity(False)

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
        return self.status in ProjectPhase.objects.filter(slug__in=['done-complete', 'done-incomplete', 'realised']).all()

    @property
    def is_funding(self):
        return self.amount_asked > 0

    def supporters_count(self, with_guests=True):
        # TODO: Replace this with a proper Supporters API
        # something like /projects/<slug>/donations
        donations = self.donation_set
        donations = donations.filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])
        donations = donations.filter(order__user__isnull=False)
        donations = donations.annotate(Count('order__user'))
        count = len(donations.all())

        if with_guests:
            donations = self.donation_set
            donations = donations.filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])
            donations = donations.filter(order__user__isnull=True)
            count += len(donations.all())
        return count

    @property
    def task_count(self):
        from bluebottle.utils.model_dispatcher import get_task_model
        TASK_MODEL = get_task_model()
        return len(self.task_set.filter(status=TASK_MODEL.TaskStatuses.open).all())

    @property
    def get_open_tasks(self):
        from bluebottle.utils.model_dispatcher import get_task_model
        TASK_MODEL = get_task_model()
        return self.task_set.filter(status=TASK_MODEL.TaskStatuses.open).all()

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
    def donated_percentage(self):
        if not self.amount_asked:
            return 0
        elif self.amount_donated > self.amount_asked:
            return 100
        return int(100 * self.amount_donated / self.amount_asked)

    @models.permalink
    def get_absolute_url(self):
        """ Get the URL for the current project. """
        return 'project-detail', (), {'slug': self.slug}

    def get_absolute_frontend_url(self):
        url = self.get_absolute_url()
        # insert the hashbang, after the language string
        bits = url.split('/')
        url = "/".join(bits[:2] + ['#!'] + bits[2:])
        return url

    def get_meta_title(self, **kwargs):
        return u"%(name_project)s | %(theme)s | %(country)s" % {
            'name_project': self.title,
            'theme': self.theme.name if self.theme else '',
            'country': self.country.name if self.country else '',
        }

    def get_fb_title(self, **kwargs):
        title = _(u"{name_project} in {country}").format(
                    name_project = self.title,
                    country = self.country.name if self.country else '',
                )
        return title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(lang_code, settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_fb_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u"{title} {{URL}}").format(
                    title=title, twitter_handle=twitter_handle
                )

        return tweet

    class Meta(BaseProject.Meta):
        ordering = ['title']
        default_serializer = 'bluebottle.projects.serializers.ProjectSerializer'
        preview_serializer = 'bluebottle.projects.serializers.ProjectPreviewSerializer'
        manage_serializer = 'bluebottle.projects.serializers.ManageProjectSerializer'

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title)
            counter = 2
            qs = Project.objects
            while qs.filter(slug = original_slug).exists():
                original_slug = '%s-%d' % (original_slug, counter)
                counter += 1
            self.slug = original_slug

        #There are 9 ProjectPhase objects: 1. Plan - New, 2. Plan - Submitted, 3. Plan - Needs Work, 4. Plan - Rejected,
        #5. Campaign, 6. Stopped, 7. Done - Complete, 8. Done - Incomplete, 9. Done - Stopped.
        if not self.status:
            self.status = ProjectPhase.objects.get(slug="plan-new")

        #If the project status is moved to New or Needs Work, clear the date_submitted field
        if self.status in ProjectPhase.objects.filter(Q(slug="plan-new")|Q(slug="plan-needs-work")):
            self.date_submitted = None

        #Set the submitted date
        if self.status == ProjectPhase.objects.get(slug="plan-submitted") and not self.date_submitted:
            self.date_submitted = timezone.now()

        #Set the campaign started date
        if self.status == ProjectPhase.objects.get(slug="campaign") and not self.campaign_started:
            self.campaign_started = timezone.now()

        #Set a default deadline of 30 days
        if not self.deadline:
            self.deadline = timezone.now() + datetime.timedelta(days=30)

        # make sure the deadline is set to the end of the day, amsterdam time
        tz = pytz.timezone('Europe/Amsterdam')
        local_time = self.deadline.astimezone(tz)
        if local_time.time() != datetime.time(23, 59, 59):
            self.deadline = tz.localize(
                datetime.datetime.combine(local_time.date(), datetime.time(23, 59, 59))
            )

        if self.amount_asked:
            self.update_amounts(False)

        #Project is not ended, complete, funded or stopped and its deadline has expired.
        if not self.campaign_ended and self.status not in ProjectPhase.objects.filter(Q(slug="done-complete") |
                                                           Q(slug="done-incomplete") |
                                                           Q(slug="done-stopped")) and self.deadline < timezone.now():
            if self.amount_donated >= self.amount_asked:
                self.status = ProjectPhase.objects.get(slug="done-complete")
            elif self.amount_donated <= 20 or not self.campaign_started:
                self.status = ProjectPhase.objects.get(slug="closed")
            else:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
            self.campaign_ended = self.deadline

        if self.status in ProjectPhase.objects.filter(Q(slug="done-complete") |
                                                           Q(slug="done-incomplete") |
                                                           Q(slug="done-stopped")) and not self.campaign_ended:
            self.campaign_ended = timezone.now()

        super(Project, self).save(*args, **kwargs)

    def status_changed(self, old_status, new_status):
        status_complete = ProjectPhase.objects.get(slug="done-complete")
        status_incomplete = ProjectPhase.objects.get(slug="done-incomplete")

        if new_status == status_complete:
            mail_project_complete(self)
        if new_status == status_incomplete:
            mail_project_incomplete(self)

    def deadline_reached(self):
        # BB-3616 "Funding projects should not look at (in)complete tasks for their status."
        from bluebottle.utils.model_dispatcher import get_task_model
        TASK_MODEL = get_task_model()

        if self.is_funding:
            if self.amount_donated >= self.amount_asked:
                self.status = ProjectPhase.objects.get(slug="done-complete")
            elif self.amount_donated <= 20 or not self.campaign_started:
                self.status = ProjectPhase.objects.get(slug="closed")
            else:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
        else:
            if self.task_set.filter(status__in=[TASK_MODEL.TaskStatuses.in_progress,
                                                TASK_MODEL.TaskStatuses.open]).count() > 0:
                self.status = ProjectPhase.objects.get(slug="done-incomplete")
            else:
                self.status = ProjectPhase.objects.get(slug="done-complete")
        self.campaign_ended = now()
        self.save()

class ProjectBudgetLine(models.Model):
    """
    BudgetLine: Entries to the Project Budget sheet.
    This is the budget for the amount asked from this
    website.
    """
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
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


class PartnerOrganization(models.Model):
    """
        Some projects are run in cooperation with a partner
        organization like EarthCharter & MacroMicro
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    description = models.TextField(_("description"))
    image = ImageField(_("image"), max_length=255, blank=True, null=True, upload_to='partner_images/', help_text=_("Main partner picture"))

    @property
    def projects(self):
        return self.project_set.order_by('-favorite', '-popularity').filter(status__in=[ProjectPhase.objects.get(slug="campaign"),
                                                                            ProjectPhase.objects.get(slug="done-complete"),
                                                                            ProjectPhase.objects.get(slug="done-incomplete")])

    class Meta:
        db_table = 'projects_partnerorganization'
        verbose_name = _("partner organization")
        verbose_name_plural = _("partner organizations")

    def __unicode__(self):
        if self.name:
            return self.name
        return self.slug


@receiver(project_funded, weak=False, sender=Project, dispatch_uid="email-project-team-project-funded")
def email_project_team_project_funded(sender, instance, first_time_funded, **kwargs):
    mail_project_funded_internal(instance)


@receiver(post_init, sender=Project, dispatch_uid="bluebottle.projects.Project.post_init")
def project_post_init(sender, instance, **kwargs):
    try:
        instance._init_status = instance.status
    except ProjectPhase.DoesNotExist:
        instance._init_status = None

@receiver(post_save, sender=Project, dispatch_uid="bluebottle.projects.Project.post_save")
def project_post_save(sender, instance, **kwargs):
    try:
        init_status, current_status = None, None

        try:
            init_status = instance._init_status
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

