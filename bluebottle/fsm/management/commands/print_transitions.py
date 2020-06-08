from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from bluebottle.funding.models import Donation, Funding
from bluebottle.members.models import Member


def get_doc(element):
    if element.__doc__:
        return element.__doc__
    return "{} (documentation missing)".format(unicode(element))


class Command(BaseCommand):
    help = 'Prints transitions for a model'

    def add_arguments(self, parser):
        parser.add_argument(
            'model',
            type=str,
            help='Dotted path to the model'
        )
        parser.add_argument(
            '--attributes',
            type=str,
            default='',
            help='List of comma separated attributes, e.g. "title=bla,description=test'
        )
        parser.add_argument(
            '--owner',
            type=str,
            help='Email of the models owner'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Email of the models user'
        )

    def _has_field(self, model, field):
        try:
            model._meta.get_field(field)
            return True
        except FieldDoesNotExist:
            return False

    def handle(self, *args, **options):
        model = import_string(options['model'])

        if options['attributes']:
            model_args = dict(
                arg.split('=') for arg in options.get('attributes', ).split(",")
            )
        else:
            model_args = {}

        if options.get('owner') and self._has_field(model, 'owner'):
            model_args['owner'] = Member(email=options['owner'])

        if options.get('user') and self._has_field(model, 'user'):
            model_args['user'] = Member(email=options['user'])

        instance = model(
            **model_args
        )

        if isinstance(instance, Funding):
            instance.title = 'campaign'

        if isinstance(instance, Donation):
            instance.activity = Funding(title='campaign')

        machine = instance.states

        text = ''

        # text += u'# {}\n'.format(model._meta.model_name.capitalize())

        text += u'## States\n'

        text += u'|State Name|Description|\n'
        text += u'|---|---|\n'

        for state in machine.states.values():
            text += u'|{}|{}|\n'.format(state.name.capitalize(), state.description)

        text += u'\n'

        text += u'## Transitions\n'
        text += u'|Name|Description|From|To|Manual|Conditions|Side Effects|\n'
        text += u'|---|---|---|---|---|--------|--------|\n'

        for transition in machine.transitions.values():
            text += u'|{}|{}|{}|{}|{}|{}|{}|\n'.format(
                transition.name,
                transition.description,
                ', '.join(state.name.capitalize() for state in transition.sources),
                transition.target.name.capitalize(),
                'Automatic' if transition.automatic else 'Manual',
                ', '.join(
                    get_doc(condition)
                    for condition
                    in transition.conditions
                ),
                ', '.join(
                    unicode(effect(instance))
                    for effect
                    in transition.effects
                ),
            )
        text += u'\n'

        if model.triggers:
            text += u'# Triggers\n'
            text += u'|When|Conditions|Effects|\n'
            text += u'|---|---|---|\n'

            for trigger in model.triggers:
                for effect in trigger.effects:
                    text += u'|{}|{}|{}|\n'.format(
                        unicode(trigger(instance)),
                        ' or '.join(get_doc(condition) for condition in effect.conditions),
                        unicode(effect(instance)),
                    )

        print(text)
