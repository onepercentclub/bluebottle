from builtins import object
from builtins import str

from adminsortable.models import SortableMixin
from django.db import models
from django.db.models import Sum
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible
from memoize import memoize
from parler.models import TranslatedFields, TranslatableModel
from polymorphic.models import PolymorphicModel

from bluebottle.impact.models import ICONS
from bluebottle.statistics.statistics import Statistics
from bluebottle.utils.managers import TranslatablePolymorphicManager
from bluebottle.utils.models import get_language_choices


@python_2_unicode_compatible
class BaseStatistic(PolymorphicModel, SortableMixin):

    objects = TranslatablePolymorphicManager()

    active = models.BooleanField(
        help_text=_('Should this be shown or hidden.'),
        default=True
    )
    sequence = models.PositiveIntegerField(
        help_text=_('Order in which metrics are shown.'),
        default=0, editable=False, db_index=True)

    def __str__(self):
        for child in (DatabaseStatistic, ManualStatistic, ImpactStatistic):
            try:
                return u"{}".format(getattr(self, child.__name__.lower()).name)
            except child.DoesNotExist:
                pass
        return u"Stat #{}".format(self.id)

    class Meta(object):
        ordering = ['sequence']
        verbose_name = _('Statistic')
        verbose_name_plural = _('Statistics')


class ManualStatistic(BaseStatistic, TranslatableModel):
    value = models.IntegerField()
    objects = TranslatablePolymorphicManager()
    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=100)
    )

    icon = models.CharField(
        _('icon'), choices=ICONS,
        null=True, blank=True, max_length=20
    )

    timeout = 3600

    def get_value(self, start=None, end=None, subregion=None, user=None):
        return self.value

    unit = None

    class JSONAPIMeta(object):
        resource_name = 'statistics/manual-statistics'

    def __str__(self):
        return str(self.translations.name)

    class Meta(object):
        verbose_name = _('Custom statistic')
        verbose_name_plural = _('Custom statistics')


class DatabaseStatistic(BaseStatistic, TranslatableModel):
    QUERIES = [
        ('people_involved', _('People involved')),
        ('participants', _('Participants')),

        ('activities_succeeded', _('Activities succeeded')),
        ('time_activities_succeeded', _('Time based activities succeeded')),
        ('fundings_succeeded', _('Crowdfunding campaigns succeeded')),
        ('deeds_succeeded', _('Deeds succeeded')),

        ('activity_participants', _('Activity Participants')),

        ('time_activities_online', _('Time based activities online')),
        ('deeds_online', _('Deeds online')),
        ('fundings_online', _('Funding activities online')),

        ('donations', _('Donations')),
        ('donated_total', _('Donated total')),
        ('pledged_total', _('Pledged total')),
        ('amount_matched', _('Amount matched')),
        ('activities_online', _('Activities Online')),
        ('time_spent', _('Time spent')),
        ('deeds_done', _('Deeds done')),
        ('collect_done', _('Collect done')),
        ('members', _("Number of members"))
    ]
    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=100)
    )
    objects = TranslatablePolymorphicManager()

    query = models.CharField(
        _('query'),
        max_length=30,
        choices=QUERIES,
        db_index=True
    )
    unit = None

    @property
    def icon(self):
        mapping = {

            'people_involved': 'people',
            'participants': 'people',

            'activities_succeeded': 'default',
            'time_activities_succeeded': 'event-completed',
            'deed_succeeded': 'deed-completed',
            'fundings_succeeded': 'funding-completed',
            'fundings_online': 'funding',
            'time_activities_online': 'event',
            'deeds_activities_online': 'deed',

            'donations': 'money',
            'donated_total': 'money',
            'pledged_total': 'money',
            'amount_matched': 'money',

            'activities_online': 'default',

            'time_spent': 'time',

            'deeds_done': 'deeds',

            'collect_done': 'collect',

            'members': 'people',
        }
        return mapping.get(self.query)

    @memoize(timeout=3600)
    def get_value(self, start=None, end=None, subregion=None, user=None):
        return getattr(Statistics(start, end, subregion, user), self.query)

    def __str__(self):
        return str(self.query)

    class JSONAPIMeta(object):
        resource_name = 'statistics/database-statistics'

    class Meta(object):
        verbose_name = _('Engagement statistic')
        verbose_name_plural = _('Engagement statistics')


class ImpactStatistic(BaseStatistic):
    impact_type = models.ForeignKey('impact.ImpactType', on_delete=models.CASCADE)

    def get_value(self, start=None, end=None, subregion=None, user=None):
        goals = self.impact_type.goals.filter(
            activity__status='succeeded',
        )

        if start and end:
            goals = goals.filter(
                activity__created__gte=start,
                activity__created__lt=end,
            )

        return goals.aggregate(
            sum=Sum('realized')
        )['sum'] or 0

    @property
    def unit(self):
        return self.impact_type.unit

    @property
    def icon(self):
        if not self.impact_type:
            return 'default'
        return self.impact_type.icon

    @property
    def name(self):
        return str(self.impact_type.text_passed)

    def __str__(self):
        return str(self.impact_type.name)

    class JSONAPIMeta(object):
        resource_name = 'statistics/impact-statistics'

    class Meta(object):
        verbose_name = _('Impact statistic')
        verbose_name_plural = _('Impact statistics')


class Statistic(models.Model):
    """
    Statistics for homepage
    """
    class StatisticType(DjangoChoices):
        manual = ChoiceItem('manual', label=_("Manual"))
        donated_total = ChoiceItem('donated_total', label=_("Donated total"))
        pledged_total = ChoiceItem('pledged_total', label=_("Pledged total"))
        tasks_realized = ChoiceItem(
            'tasks_realized', label=_("Tasks realized"))
        task_members = ChoiceItem('task_members', label=_("Taskmembers"))
        people_involved = ChoiceItem(
            'people_involved', label=_("People involved"))
        participants = ChoiceItem('participants', label=_("Participants"))
        amount_matched = ChoiceItem(
            'amount_matched', label=_("Amount Matched"))
        votes_cast = ChoiceItem('votes_cast', label=_("Number of votes cast"))
        members = ChoiceItem('members', label=_("Number of members"))

    title = models.CharField(_("Title"), max_length=100, blank=True)

    type = models.CharField(_('Type'), max_length=20,
                            choices=StatisticType.choices,
                            default=StatisticType.manual, db_index=True)
    sequence = models.IntegerField()
    value = models.CharField(
        null=True, blank=True, max_length=12,
        help_text=_('This overwrites the calculated value, if available')
    )
    active = models.BooleanField(
        help_text=_('Should this be shown or hidden.'))

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('last modification'), auto_now=True)

    language = models.CharField(
        _('language'),
        max_length=7,
        blank=True,
        null=True,
        choices=lazy(get_language_choices, tuple)())

    def __str__(self):
        return self.title

    @property
    def statistics(self):
        return Statistics()

    @property
    def calculated_value(self):
        if self.value:
            return self.value

        return getattr(self.statistics, self.type, 0)

    class Meta(object):
        ordering = ('sequence', )
