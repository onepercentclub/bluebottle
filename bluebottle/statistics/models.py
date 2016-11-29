from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import lazy

from djchoices import DjangoChoices, ChoiceItem
from django_extensions.db.fields import CreationDateTimeField, \
    ModificationDateTimeField

from bluebottle.clients import properties
from bluebottle.statistics.statistics import Statistics


def get_languages():
    return properties.LANGUAGES


class Statistic(models.Model):
    """
    Statistics for homepage
    """

    class StatisticType(DjangoChoices):
        manual = ChoiceItem('manual', label=_("Manual"))
        donated_total = ChoiceItem('donated_total', label=_("Donated total"))
        projects_online = ChoiceItem('projects_online', label=_("Projects online"))
        projects_realized = ChoiceItem('projects_realized', label=_("Projects realized"))
        tasks_realized = ChoiceItem('tasks_realized', label=_("Tasks realized"))
        people_involved = ChoiceItem('people_involved', label=_("People involved"))
        votes_cast = ChoiceItem('votes_cast', label=_("Number of votes cast"))

    title = models.CharField(_("Title"), max_length=100, blank=True)

    type = models.CharField(_('Type'), max_length=20,
                            choices=StatisticType.choices,
                            default=StatisticType.manual, db_index=True)
    sequence = models.IntegerField()
    value = models.CharField(null=True, blank=True, max_length=12, help_text=_('This overwrites the calculated value, if available'))
    active = models.BooleanField(help_text=_('Should this be shown or hidden.'))
    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))
    language = models.CharField(
        _('language'),
        max_length=5,
        blank=True,
        null=True,
        choices=lazy(get_languages, tuple)())

    def __unicode__(self):
        return self.title

    @property
    def calculated_value(self):
        if self.value:
            return self.value
        return getattr(Statistics(), self.type, 0)

    class Meta:
        ordering = ('sequence', )
