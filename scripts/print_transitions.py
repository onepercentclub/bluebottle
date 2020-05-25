from collections import defaultdict

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine
from bluebottle.funding.states import FundingStateMachine, DonationStateMachine, PayoutAccountStateMachine, \
    PayoutStateMachine
from bluebottle.funding_stripe.states import StripeSourcePaymentStateMachine, StripePaymentStateMachine
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.notifications.effects import BaseNotificationEffect
from bluebottle.fsm.effects import BaseTransitionEffect, BaseRelatedTransitionEffect
from bluebottle.fsm.state import Transition
from bluebottle.fsm.triggers import ModelTrigger

machines = [
    ReviewStateMachine, OrganizerStateMachine,
    EventStateMachine, ParticipantStateMachine,
    AssignmentStateMachine, ApplicantStateMachine,
    FundingStateMachine, DonationStateMachine,
    PayoutAccountStateMachine, PayoutStateMachine,
    StripeSourcePaymentStateMachine, StripePaymentStateMachine
]


def describe_effect(effect, machine):
    description = ''
    if issubclass(effect, BaseNotificationEffect):
        description = 'Send message "{}"'.format(effect.message.subject)
    elif issubclass(effect, BaseRelatedTransitionEffect):
        description = '{} related {}'.format(
            effect.transition_effect_class.name,
            effect.relation
        ).capitalize()

    elif issubclass(effect, BaseTransitionEffect):
        transition = machine.transitions[effect.name]
        description = 'Transition from {} to "{}"'.format(
            ', '.join(unicode(source.name) for source in transition.sources),
            unicode(transition.target.name)
        )
    else:
        description = effect.__doc__.capitalize()

    if effect.conditions:
        description += ', when {}'.format(
            ' and '.join(condition.__doc__ for condition in effect.conditions)
        )

    return description


def describe_transition(name, transition, machine):
    print '#### {}\n'.format(name.capitalize())
    print '{} transition from {} to "{}"\n'.format(
        'Automatic' if transition.automatic else 'Manual',
        ', '.join(unicode(source.name) for source in transition.sources),
        unicode(transition.target.name)
    )

    if transition.effects:
        print 'Side effects:\n'
        for effect in transition.effects:
            print '* {}'.format(describe_effect(effect, machine))

    print '\n'


def describe_trigger(effect, trigger):
    if isinstance(trigger, Transition):
        description = 'When transitioning to {}'.format(trigger.target.name)

    elif issubclass(trigger, ModelTrigger):
        if trigger.field:
            description = "When the {} has changed".format(trigger.field)
        else:
            description = 'When {}'.format(trigger.is_valid.__doc__.lower())

    if effect.conditions:
        description += ', and {}'.format(
            ' and '.join(condition.__doc__ for condition in effect.conditions)
        )
    print '* {}'.format(description)


def run(*args, **kwargs):
    for machine_class in machines:
        instance = machine_class.model()
        machine = machine_class(instance)
        triggers = defaultdict(list)

        for trigger in machine_class.model.triggers:
            for effect in trigger.effects:
                if issubclass(effect, BaseTransitionEffect) and effect.name in machine.transitions:
                    transition = machine.transitions[effect.name]
                    triggers[transition.target].append((effect, trigger))

        for transition in machine_class.transitions.values():
            for effect in transition.effects:
                if issubclass(effect, BaseTransitionEffect) and effect.name in machine.transitions:
                    transition = machine.transitions[effect.name]
                    triggers[transition.target].append((effect, transition))

        print '# {}\n'.format(machine.model._meta.verbose_name)

        print '## State: Initial\n'
        initial = machine.initial_transition
        describe_transition('initial', initial, machine)

        for value, state in machine.states.items():

            print '\n## State: {}\n'.format(state.name)
            print '{}\n'.format(state.description)

            print '\n### Triggers'
            for effect, trigger in triggers[state]:
                describe_trigger(effect, trigger)

            print '\n### Transitions'

            for name, transition in (
                (name, transition) for name, transition in machine.transitions.items()
                if state in transition.sources
            ):
                describe_transition(name, transition, machine)
