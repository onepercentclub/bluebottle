from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

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

    def handle(self, *args, **options):
        model = import_string(options['model'])

        if options['attributes']:
            model_args = dict(
                arg.split('=') for arg in options.get('attributes', ).split(",")
            )
        else:
            model_args = {}

        if options.get('owner'):
            model_args['owner'] = Member(email=options['owner'])

        if options.get('user'):
            model_args['user'] = Member(email=options['user'])

        instance = model(
            **model_args
        )
        machine = instance.states

        print '# {}\n'.format(model._meta.model_name.capitalize())

        print '## States\n'

        print '|State Name|Description|'
        print '|---|---|'

        for state in machine.states.values():
            print '|{}|{}|'.format(state.name.capitalize(), state.description)

        print '\n'

        print '## Transitions\n'
        print '|Name|Description|From|To|Manual|Conditions|Side Effects|'
        print '|---|---|---|---|---|--------|--------|'

        for transition in machine.transitions.values():
            print '| {} | {} | {} | {} | {} | {} | {} |'.format(
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
                    unicode(effect(instance)) for effect in transition.effects
                ),
            )

        print '\n'

        if model.triggers:
            print '# Triggers\n'
            print '|When|Effects|'
            print '|---|---|'

            for trigger in model.triggers:
                print '|{}|{}|'.format(
                    unicode(trigger),
                    ', '.join(unicode(effect(instance)) for effect in trigger.effects)
                )
