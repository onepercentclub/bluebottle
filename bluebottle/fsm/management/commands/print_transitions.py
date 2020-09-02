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
    return "{} (documentation missing)".format(str(element)).replace('<', '').replace('>', '')


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
            instance.title = "the initiative"

        if isinstance(instance, Funding):
            instance.title = "the campaign"

        if isinstance(instance, Donation):
            instance.activity = Funding(title="the campaign")
            instance.user = Member(first_name='the', last_name='donor')

        if isinstance(instance, Event):
            instance.title = "the event"

        if isinstance(instance, Participant):
            instance.activity = Event(title="the event")
            instance.user = Member(first_name='the', last_name='participant')

        if isinstance(instance, Assignment):
            instance.title = "the assignment"

        if isinstance(instance, Applicant):
            instance.activity = Assignment(title="the assignment")
            instance.user = Member(first_name='the', last_name='applicant')

        machine = instance.states

        text = ""

        text += "<h2>States</h2>"
        text += "<em>All states this instance can be in.</em>"

        text += "<table data-layout=\"default\"><tr><th>State Name</th><th>Description</th></tr>"

        for state in list(machine.states.values()):
            text += "<tr><td>{}</td><td>{}</td></tr>".format(state.name.capitalize(), state.description)

        text += "</table>"

        text += "<h2>Transitions</h2>"
        text += "<em>An instance will always move from one state to the other through a transition. " \
                "A manual transition is initiated by a user. An automatic transition is initiated by the system, " \
                "either through a trigger or through a side effect of a related object.</em>"
        text += "<table data-layout=\"full-width\"><tr><th>Name</th><th>Description</th><th>From</th><th>To</th>" \
                "<th>Manual</th><th>Conditions</th><th>Side Effects</th></tr>"

        for transition in list(machine.transitions.values()):
            str = "<tr><td>{}</td><td>{}</td><td><ul>{}</ul></td>" \
                  "<td>{}</td><td>{}</td><td><ul>{}</ul></td><td><ul>{}</ul></td></tr>"

            text += str.format(
                transition.name,
                transition.description,
                "".join("<li>{}</li>".format(state.name.capitalize()) for state in transition.sources),
                transition.target.name.capitalize(),
                "Automatic" if transition.automatic else "Manual",
                "".join(
                    "<li>{}</li>".format(get_doc(condition))
                    for condition
                    in transition.conditions
                ),
                "".join(
                    "<li>{}</li>".format(effect(instance).to_html())
                    for effect
                    in transition.effects
                )
            )
        text += "</table>"

        if model.triggers:
            text += "<h2>Triggers</h2>"
            text += "<em>These are events that get triggered when the instance changes, " \
                    "other then through a transition. " \
                    "Mostly it would be triggered because a property changed (e.g. a deadline).</em>"
            text += "<table data-layout=\"full-width\">" \
                    "<tr><th>When</th>" \
                    "<th>Effects</th></tr>"

            for trigger in model.triggers:
                text += "<tr><td>{}</td><td><ul>{}</ul></td></tr>".format(
                    str(trigger(instance)),
                    "".join(["<li>{}</li>".format(effect(instance).to_html()) for effect in trigger(instance).effects])
                )
            text += "</table>"

        if model.triggers:
            text += "<h2>Periodic tasks</h2>"
            text += "<em>These are events that get triggered when certain dates are passed. " \
                    "Every 15 minutes the system checks for passing deadlines, registration dates and such.</em>"

            text += "<table data-layout=\"full-width\">" \
                    "<tr><th>When</th>" \
                    "<th>Effects</th></tr>"

            for task in model.periodic_tasks:
                text += "<tr><td>{}</td><td><ul>{}</ul></td></tr>".format(
                    str(task(instance)),
                    "".join(["<li>{}</li>".format(effect(instance).to_html()) for effect in task(instance).effects])
                )
            text += "</table>"
        print(text)
