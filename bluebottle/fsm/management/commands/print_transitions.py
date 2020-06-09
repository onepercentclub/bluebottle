from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.events.models import Event, Participant
from bluebottle.funding.models import Donation, Funding
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member


def get_doc(element):
    if element.__doc__:
        return element.__doc__
    return "{} (documentation missing)".format(unicode(element)).replace('<', '').replace('>', '')


class Command(BaseCommand):
    help = "Prints transitions for a model"

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            type=str,
            help="Dotted path to the model"
        )
        parser.add_argument(
            "--attributes",
            type=str,
            default="",
            help="List of comma separated attributes, e.g. 'title=bla,description=test'"
        )
        parser.add_argument(
            "--owner",
            type=str,
            help="Email of the models owner"
        )
        parser.add_argument(
            "--user",
            type=str,
            help="Email of the models user"
        )

    def _has_field(self, model, field):
        try:
            model._meta.get_field(field)
            return True
        except FieldDoesNotExist:
            return False

    def handle(self, *args, **options):
        model = import_string(options["model"])

        if options["attributes"]:
            model_args = dict(
                arg.split("=") for arg in options.get("attributes", ).split(",")
            )
        else:
            model_args = {}

        if options.get("owner") and self._has_field(model, "owner"):
            model_args["owner"] = Member(email=options["owner"])

        if options.get("user") and self._has_field(model, "user"):
            model_args["user"] = Member(email=options["user"])

        instance = model(
            **model_args
        )

        if isinstance(instance, Initiative):
            instance.title = "Demo Initiative"

        if isinstance(instance, Funding):
            instance.title = "Demo Campaign"

        if isinstance(instance, Donation):
            instance.activity = Funding(title="Demo Campaign")

        if isinstance(instance, Event):
            instance.title = "Demo Event"

        if isinstance(instance, Participant):
            instance.activity = Event(title="Demo Event")

        if isinstance(instance, Assignment):
            instance.title = "Demo Assignment"

        if isinstance(instance, Applicant):
            instance.activity = Assignment(title="Demo Assignment")

        machine = instance.states

        text = ""

        text += u"<h2>States</h2>"

        text += u"<table data-layout=\"default\"><tr><th>State Name</th><th>Description</th></tr>"

        for state in machine.states.values():
            text += u"<tr><td>{}</td><td>{}</td></tr>".format(state.name.capitalize(), state.description)

        text += u"</table>"

        text += u"<h2>Transitions</h2>"
        text += u"<table data-layout=\"full-width\"><tr><th>Name</th><th>Description</th><th>From</th><th>To</th>" \
                u"<th>Manual</th><th>Conditions</th><th>Side Effects</th></tr>"

        for transition in machine.transitions.values():
            str = u"<tr><td>{}</td><td>{}</td><td><ul>{}</ul></td>" \
                  u"<td>{}</td><td>{}</td><td><ul>{}</ul></td><td><ul>{}</ul></td></tr>"
            text += str.format(
                transition.name,
                transition.description,
                u"".join(u"<li>{}</li>".format(state.name.capitalize()) for state in transition.sources),
                transition.target.name.capitalize(),
                "Automatic" if transition.automatic else "Manual",
                u"".join(
                    u"<li>{}</li>".format(get_doc(condition))
                    for condition
                    in transition.conditions
                ),
                u"".join(
                    u"<li>{}</li>".format(effect(instance).to_html())
                    for effect
                    in transition.effects
                ),
            )
        text += u"</table>"

        if model.triggers:
            text += u"<h2>Triggers</h2>"
            text += u"<table data-layout=\"full-width\">" \
                    u"<tr><th>When</th>" \
                    u"<th>Conditions</th>" \
                    u"<th>Effects</th></tr>"

            for trigger in model.triggers:
                for effect in trigger(instance).effects:
                    text += u"<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                        unicode(trigger(instance)),
                        u" <b>and</b> ".join(get_doc(condition) for condition in effect(instance).conditions),
                        effect(instance).to_html(),
                    )
            text += u"</table>"
        print(text)
