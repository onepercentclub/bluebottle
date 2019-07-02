from django.utils.translation import ugettext_lazy as _

from djchoices.choices import ChoiceItem

from bluebottle.fsm import transition
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions


class AssignmentTransitions(ActivityTransitions):
    @transition(
        field='status',
        source=ActivityTransitions.values.open,
        target=ActivityTransitions.values.running,
    )
    def start(self, **kwargs):
        pass

    @transition(
        field='status',
        source=ActivityTransitions.values.running,
        target=ActivityTransitions.values.done,
    )
    def success(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.success()
            member.save()

    @transition(
        field='status',
        source=ActivityTransitions.values.running,
        target=ActivityTransitions.values.closed,
    )
    def close(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.fail()
            member.save()

    @transition(
        field='status',
        source=[
            ActivityTransitions.values.closed,
            ActivityTransitions.values.done,
            ActivityTransitions.values.running
        ],
        target=ActivityTransitions.values.open,
    )
    def extend_deadline(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[
            ActivityTransitions.values.closed,
            ActivityTransitions.values.done
        ],
        target=ActivityTransitions.values.running,
    )
    def extend(self, **kwargs):
        pass


class ApplicantTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        accepted = ChoiceItem('accepted', _('accepted'))
        rejected = ChoiceItem('rejected', _('rejected'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        active = ChoiceItem('attending', _('done'))

    @property
    def assignment_is_open(self):
        return self.instance.activity.status == ActivityTransitions.values.open

    @transition(
        field='status',
        source=[values.new, values.rejected],
        target=values.accepted,
        conditions=[assignment_is_open]
    )
    def accept(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.rejected,
        conditions=[assignment_is_open]
    )
    def reject(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.withdrawn,
        conditions=[assignment_is_open]
    )
    def withdraw(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=values.accepted,
        target=values.active,
    )
    def activate(self):
        pass

    @transition(
        field='status',
        source=[values.active, values.failed],
        target=values.success,
    )
    def success(self):
        pass

    @transition(
        field='status',
        source=[values.success, values.active],
        target=values.failed,
    )
    def fail(self):
        self.time_spent = None
