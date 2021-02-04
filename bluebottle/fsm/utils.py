import re
from datetime import timedelta

from django.core.exceptions import FieldDoesNotExist
from django.utils.timezone import now

from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.funding.models import Donor, Funding, PayoutAccount, Payment, MoneyContribution
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import DateActivity, PeriodActivity, DateParticipant, PeriodParticipant, \
    TimeContribution, DateActivitySlot, SlotParticipant


def get_doc(element):
    if element.__doc__:
        return element.__doc__
    return "{} (documentation missing)".format(str(element)).replace('<', '').replace('>', '')


def has_field(model, field):
    try:
        model._meta.get_field(field)
        return True
    except FieldDoesNotExist:
        return False


def clean(string):
    return re.sub(' +', ' ', string.replace("\n", " "))


def document_model(model):
    documentation = {
        'states': [],
        'transitions': [],
        'triggers': [],
        'periodic_tasks': []
    }

    model_args = {}

    if has_field(model, "owner"):
        model_args["owner"] = Member(email='initiator@example.com')

    if has_field(model, "user"):
        model_args["user"] = Member(email='supporter@example.com')

    instance = model(
        **model_args
    )

    if isinstance(instance, Initiative):
        instance.title = "the initiative"

    if isinstance(instance, Funding):
        instance.title = "the campaign"

    if isinstance(instance, Donor):
        PledgePayment(donation=instance)
        instance.activity = Funding(title="the campaign")
        instance.user = Member(first_name='the', last_name='donor')

    if isinstance(instance, MoneyContribution):
        donor = Donor()
        donor.activity = Funding(title="the campaign")
        donor.user = Member(first_name='the', last_name='donor')
        PledgePayment(donation=donor)
        instance.contributor = donor

    if isinstance(instance, Payment):
        instance.donation = Donor()

    if isinstance(instance, PeriodActivity):
        instance.title = "the activity"
        instance.owner = Member(first_name='activity', last_name='owner')

    if isinstance(instance, PeriodParticipant):
        instance.activity = PeriodActivity(title="the activity")
        instance.user = Member(first_name='the', last_name='participant')

    if isinstance(instance, DateActivity):
        instance.title = "the activity"
        instance.owner = Member(first_name='activity', last_name='owner')

    if isinstance(instance, DateParticipant):
        instance.activity = DateActivity(title="the activity")
        instance.user = Member(first_name='the', last_name='participant')

    if isinstance(instance, DateActivitySlot):
        instance.activity = DateActivity(title="the activity")

    if isinstance(instance, SlotParticipant):
        activity = DateActivity(title="the activity")
        instance.slot = DateActivitySlot(activity=activity)
        instance.participant = DateParticipant(activity=activity)

    if isinstance(instance, TimeContribution):
        contributor = PeriodParticipant()
        contributor.activity = PeriodActivity(title="the activity")
        contributor.user = Member(first_name='the', last_name='participant')
        instance.contributor = contributor
        instance.start = now() + timedelta(days=4)
        instance.value = timedelta(hours=4)

    if isinstance(instance, PayoutAccount):
        instance.owner = Member(first_name='the', last_name='owner')

    machine = instance.states
    for state in list(machine.states.values()):
        documentation['states'].append({
            'name': state.name.capitalize(),
            'description': state.description
        })

    for transition in machine.transitions.values():
        triggers = [
            trigger for trigger in instance.triggers.triggers
            if isinstance(trigger, TransitionTrigger) and trigger.transition == transition
        ]
        effects = sum([trigger.effects for trigger in triggers], [])
        documentation['transitions'].append({
            'name': transition.name,
            'description': transition.description,
            'from': [state.name.capitalize() for state in transition.sources],
            'to': transition.target.name.capitalize(),
            'manual': "Automatic" if transition.automatic else "Manual",
            'conditions': [get_doc(condition) for condition in transition.conditions],
            'effects': [clean(effect(instance).to_html()) for effect in effects]

        })

    triggers = [
        trigger for trigger in model.triggers.triggers
        if not isinstance(trigger, TransitionTrigger)
    ]

    for trigger in triggers:
        documentation['triggers'].append({
            'when': str(trigger),
            'effects': [clean(effect(instance).to_html()) for effect in trigger.effects]
        })

    for task in model.periodic_tasks:
        documentation['periodic_tasks'].append({
            'when': str(task(instance)),
            'effects': [clean(effect(instance).to_html()) for effect in task(instance).effects]
        })

    return documentation
