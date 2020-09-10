from inspect import isclass

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import translation
from django.utils.module_loading import import_string
from djmoney.money import Money

from bluebottle.activities.models import Activity
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.funding.models import Funding, Donation, PayoutAccount
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import Member
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.test.factory_models.wallposts import TextWallpostFactory, ReactionFactory
from bluebottle.wallposts.models import Wallpost, Reaction


def get_doc(element):
    if element.__doc__:
        return element.__doc__.strip()
    return "(documentation missing)"


class Command(BaseCommand):
    help = "Prints notification messages"

    def add_arguments(self, parser):
        parser.add_argument(
            "app",
            type=str,
            help="Dotted path to the app"
        )

    def init_model(self, model):
        initiative = InitiativeFactory.create(
            title='Do Good Initiative',
            owner=self.user, reviewer=self.user,
            activity_manager=self.user, image=None
        )

        if model == Initiative:
            return initiative

        if model == Activity:
            assignment = AssignmentFactory.create(
                initiative=initiative,
                title='Do Good Task',
                owner=self.user
            )
            return assignment

        if model == Assignment:
            assignment = AssignmentFactory.create(
                initiative=initiative,
                title='Do Good Task',
                owner=self.user
            )
            return assignment

        if model == Applicant:
            assignment = AssignmentFactory.create(
                initiative=initiative,
                title='Do Good Task',
                owner=self.user
            )
            applicant = ApplicantFactory.create(
                activity=assignment,
                user=self.someone
            )
            return applicant

        if model == Event:
            event = EventFactory.create(
                initiative=initiative,
                title='Do Good Event',
                owner=self.user
            )
            return event

        if model == Participant:
            event = EventFactory.create(
                initiative=initiative,
                title='Do Good Event',
                owner=self.user
            )
            participant = ParticipantFactory.create(
                activity=event,
                user=self.someone
            )
            return participant

        if model == Funding:
            funding = FundingFactory.create(
                initiative=initiative,
                title='Do Good Funding Campaign',
                owner=self.someone
            )
            return funding

        if model == PayoutAccount:
            payout_acoount = StripePayoutAccountFactory.create(
                owner=self.user
            )
            return payout_acoount

        if model == Wallpost:
            post = TextWallpostFactory.create(
                content_object=initiative,
                author=self.someone,
                editor=self.user
            )
            return post

        if model == Reaction:
            post = TextWallpostFactory.create(
                content_object=initiative,
                author=self.someone,
                editor=self.user
            )
            reaction = ReactionFactory.create(
                wallpost=post,
                author=self.someone
            )
            return reaction

        if model == Donation:
            funding = FundingFactory.create(
                initiative=initiative,
                title='Do Good Funding Campaign',
                owner=self.user
            )
            donation = DonationFactory.create(
                activity=funding, user=self.user,
                amount=Money(35, 'EUR')
            )
            return donation

    def clean_text(self, content):
        return '\n'.join([
            line.strip() for line
            in content.strip().split('\n')
            if line.strip() and line.strip() not in ['-------------------', '-  -']
        ])

    def clean_html(self, content):
        soup = BeautifulSoup(content, "html")
        for elem in soup.find_all(['html', 'body', 'table', 'tbody', 'tr', 'td', 'th']):
            elem.unwrap()
        soup.head.extract()
        soup.contents[0].extract()
        return self.clean_text(unicode(soup))

    def handle(self, *args, **options):
        client = Client.objects.get(schema_name='goodup_demo')
        with LocalTenant(client):
            self.user, created = Member.objects.update_or_create(
                email='bart@example.com',
                defaults={
                    'first_name': 'Bart',
                    'last_name': 'Do Good'
                }
            )
            self.someone, created = Member.objects.update_or_create(
                email='anna@example.com',
                defaults={
                    'first_name': 'Anna',
                    'last_name': 'Do Good'
                }
            )
            mod = import_string("{}.messages".format(options["app"]))
            messages = [
                cls for name, cls in mod.__dict__.items()
                if isclass(cls) and cls is not TransitionMessage and issubclass(cls, TransitionMessage)
            ]
            translation.activate('en')
            text = u""
            for Message in messages:
                message = Message(self.init_model(Message.model))
                str = u"<h3>{}</h3>" \
                      u"<table>" \
                      u"<colgroup>" \
                      u"<col style='width: 150px;' />" \
                      u"<col style='width: 650x;' />" \
                      u"</colgroup>" \
                      u"<tr><th>Class</th><td>{}</td></tr>" \
                      u"<tr><th>Template</th><td>{}</td></tr>" \
                      u"<tr><th>To</th><td>{}</td></tr>" \
                      u"<tr><th>Subject</th><td>{}</td></tr>" \
                      u"</table>" \
                      u"<ac:structured-macro ac:name=\"code\"><ac:plain-text-body>" \
                      u"<![CDATA[{}]]></ac:plain-text-body></ac:structured-macro>" \
                      u"<blockquote>{}</blockquote>"
                text += str.format(
                    get_doc(message),
                    "{}.{}".format(options["app"], Message.__name__),
                    "{}.{}".format(options["app"], Message.template),
                    get_doc(message.get_recipients),
                    message.get_subject(self.user),
                    self.clean_text(message.get_content(self.user, type='txt')),
                    self.clean_html(message.get_content(self.user, type='html'))
                )

            print(text)
