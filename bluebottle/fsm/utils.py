import re
from datetime import timedelta

from django.core.exceptions import FieldDoesNotExist
from django.utils.timezone import now
from polymorphic.models import PolymorphicModel

from bluebottle.activities.models import Team
from bluebottle.collect.models import CollectActivity, CollectContributor
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.funding.models import (
    Donor,
    Funding,
    MoneyContribution,
    Payment,
    PayoutAccount,
)
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DateParticipant,
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    PeriodicParticipant,
    SlotParticipant,
    TeamSlot,
    TimeContribution,
)


def get_doc(element):
    if element.__doc__:
        return re.sub(' +', ' ', element.__doc__.replace("\n", " "))
    return "{} (documentation missing)".format(str(element)).replace('<', '').replace('>', '')


def has_field(model, field):
    try:
        model._meta.get_field(field)
        return True
    except FieldDoesNotExist:
        return False


def clean(string):
    return re.sub(' +', ' ', string.replace("\n", " "))


def setup_instance(model):
    model_args = {}

    if has_field(model, "owner"):
        model_args["owner"] = Member(email='initiator@example.com')

    if has_field(model, "user"):
        model_args["user"] = Member(email='supporter@example.com')

    instance = model(
        **model_args
    )

    if isinstance(instance, Initiative):
        instance.title = "[initiative title]"

    if isinstance(instance, Funding):
        instance.title = "[activity title]"

    if isinstance(instance, Donor):
        PledgePayment(donation=instance)
        instance.activity = Funding(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, MoneyContribution):
        donor = Donor()
        donor.activity = Funding(title="[activity title]")
        donor.activity.pre_save_polymorphic()
        donor.user = Member(first_name='[first name]', last_name='[last name]')
        PledgePayment(donation=donor)
        instance.contributor = donor

    if isinstance(instance, Payment):
        instance.donation = Donor()

    if isinstance(instance, DeadlineActivity):
        instance.title = "[activity title]"
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, DeadlineParticipant):
        instance.activity = PeriodicActivity(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, PeriodicActivity):
        instance.title = "[activity title]"
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, PeriodicParticipant):
        instance.activity = PeriodicActivity(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, DateActivity):
        instance.title = "[activity title]"
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, DateParticipant):
        instance.activity = DateActivity(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.team = Team()
        instance.team.slot = TeamSlot()
        instance.team.start = now() + timedelta(days=3)
        instance.team.duration = timedelta(hours=2)
        instance.team.owner = Member(first_name='[first name]', last_name='[last name]')
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, DateActivitySlot):
        instance.activity = DateActivity(title="[activity title]")

    if isinstance(instance, SlotParticipant):
        activity = DateActivity(title="[activity title]")
        instance.slot = DateActivitySlot(activity=activity)
        instance.participant = DateParticipant(activity=activity)

    if isinstance(instance, Team):
        instance.activity = DateActivity(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.activity.owner = Member(first_name='[first name]', last_name='[last name]')
        instance.slot = TeamSlot()
        instance.start = now() + timedelta(days=3)
        instance.duration = timedelta(hours=2)

        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, TeamSlot):
        instance.team = Team()
        instance.start = now() + timedelta(days=3)
        instance.duration = timedelta(hours=2)
        instance.team.activity = DateActivity(title="[activity title]")
        instance.team.activity.pre_save_polymorphic()
        instance.team.activity.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, TimeContribution):
        contributor = DeadlineParticipant()
        contributor.activity = DeadlineActivity(title="[activity title]")
        contributor.activity.pre_save_polymorphic()
        contributor.user = Member(first_name='[first name]', last_name='[last name]')
        instance.contributor = contributor
        instance.start = now() + timedelta(days=4)
        instance.value = timedelta(hours=4)

    if isinstance(instance, PayoutAccount):
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, Deed):
        instance.title = "[activity title]"
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, DeedParticipant):
        instance.activity = Deed(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, CollectActivity):
        instance.title = "[activity title]"
        instance.owner = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, CollectContributor):
        instance.activity = CollectActivity(title="[activity title]")
        instance.activity.pre_save_polymorphic()
        instance.user = Member(first_name='[first name]', last_name='[last name]')

    if isinstance(instance, PolymorphicModel):
        instance.pre_save_polymorphic()

    return instance


def document_model(model):
    documentation = {
        'states': [],
        'transitions': [],
        'triggers': [],
        'periodic_tasks': []
    }

    instance = setup_instance(model)

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


def document_notifications(model):
    instance = setup_instance(model)
    app = instance._meta.app_label
    messages = []
    triggers = model.triggers.triggers
    effects = []
    for trigger in triggers:
        if isinstance(trigger, TransitionTrigger):
            trigger_name = 'Transition {} on {}'.format(trigger.transition.name, instance._meta.verbose_name)
        else:
            trigger_name = '{} on {}'.format(trigger, instance._meta.verbose_name)
        for effect in trigger.effects:
            if effect.__name__ == '_NotificationEffect':
                effects.append({
                    'effect': effect,
                    'trigger': trigger_name,
                })

    for task in model.periodic_tasks:
        for effect in task(instance).effects:
            if effect.__name__ == '_NotificationEffect':
                effects.append({
                    'effect': effect,
                    'trigger': '{} on {}'.format(task(instance), instance._meta.verbose_name)
                })

    for eff in effects:
        effect = eff['effect']
        trigger = eff['trigger']
        message = effect.message(instance)
        messages.append({
            'class': "{}.{}".format(app, effect.message.__name__),
            'trigger': trigger,
            'template': effect.message.template,
            'description': get_doc(effect.message),
            'recipients': get_doc(message.get_recipients).capitalize(),
            'subject': message.generic_subject,
            'content_text': message.generic_content_text,
            # 'content_html': message.generic_content_html
        })

    return messages
