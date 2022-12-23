from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from bluebottle.fsm.effects import Effect
from bluebottle.collect.models import CollectContributor, CollectContribution


class CreateCollectContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):

        self.contribution = CollectContribution(
            contributor=self.instance,
            start=now(),
            type=self.instance.activity.collect_type
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create collect contribution'))


class SetOverallContributor(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def post_save(self):
        contributor = CollectContributor.objects.filter(user=None, activity=self.instance).first()
        if not contributor:
            contributor = CollectContributor.objects.create(
                user=None,
                activity=self.instance
            )
        contributor.value = self.instance.realized
        contributor.save()
        contribution = contributor.contributions.get()

        contribution.value = self.instance.realized
        contribution.save()

    def __str__(self):
        return str(_('Create overall contributor'))
