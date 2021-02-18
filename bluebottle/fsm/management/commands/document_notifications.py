from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from bluebottle.fsm.utils import document_notifications


def get_doc(element):
    if element.__doc__:
        return element.__doc__
    return "{} (documentation missing)".format(str(element)).replace('<', '').replace('>', '')


class Command(BaseCommand):
    help = "Prints notifications for a model"

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            type=str,
            help="Dotted path to the model"
        )

    def handle(self, *args, **options):
        model = import_string(options["model"])
        documentation = document_notifications(model)
        print(documentation)
