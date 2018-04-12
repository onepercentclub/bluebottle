import json
from datetime import timedelta, time
import httmock
import urlparse

from bluebottle.projects.admin import mark_as
from django.db.models import Count
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils import timezone
from moneyed.classes import Money

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project, ProjectPhaseLog, ProjectBudgetLine, ProjectPlatformSettings, \
    CustomProjectFieldSettings, CustomProjectField, ProjectLocation
from bluebottle.suggestions.models import Suggestion
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory, ProjectThemeFactory
from bluebottle.test.factory_models.suggestions import SuggestionFactory
from bluebottle.test.factory_models.tasks import TaskFactory, SkillFactory, TaskMemberFactory
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition
from bluebottle.utils.models import Language


class TestProjectStatusUpdate(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """

    def setUp(self):
        super(TestProjectStatusUpdate, self).setUp()

        self.init_projects()

        now = timezone.now()

        self.incomplete = ProjectPhase.objects.get(slug="done-incomplete")
        self.complete = ProjectPhase.objects.get(slug="done-complete")
        self.campaign = ProjectPhase.objects.get(slug="campaign")
        self.closed = ProjectPhase.objects.get(slug="closed")

        some_days_ago = now - timezone.timedelta(days=15)
        self.expired_project = ProjectFactory.create(
            amount_asked=5000, campaign_started=some_days_ago,
            status=self.campaign)

        self.expired_project.deadline = timezone.now() - timedelta(days=1)

    def test_deadline_end_of_day(self):
        self.expired_project.save()

        self.assertTrue(
            self.expired_project.deadline.time() == time(23, 59, 59),
            'Project deadlines are always at the end of the day'
        )

    def test_expired_too_little(self):
        """ Not enough donated - status done incomplete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=4999
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()

        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, 'needs_approval')
        self.assertEqual(self.expired_project.status, self.incomplete)

    def test_expired_under_threshold(self):
        """ Not enough donated to hit payout threshold - status closed """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=12
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()

        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, None)
        self.assertEqual(self.expired_project.status, self.closed)

    def test_expired_exact(self):
        """ Exactly the amount requested - status done complete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=5000
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()

        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, 'needs_approval')
        self.assertEqual(self.expired_project.status, self.complete)

    def test_expired_more_than_enough(self):
        """ More donated than requested - status done complete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=5001
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()
        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, 'needs_approval')
        self.failUnless(self.expired_project.status == self.complete)

        # Reopening the project should remove the payout status
        self.expired_project.status = self.campaign
        self.expired_project.deadline = timezone.now() + timedelta(days=10)
        self.expired_project.save()
        self.failUnless(self.expired_project.status == self.campaign)
        self.assertEqual(self.expired_project.payout_status, None)

    def test_expired_enough_by_matching(self):
        """ Less donated than requested  but with matching- status done complete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=2500
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()
        self.expired_project.amount_extra = Money(2500, 'EUR')
        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, 'needs_approval')
        self.failUnless(self.expired_project.status == self.complete)

    def test_expired_sourcing(self):
        """ A crowdsourcing project should never get a payout status """
        TaskFactory.create(project=self.expired_project, status='realized')
        self.expired_project.amount_asked = 0
        self.expired_project.save()
        self.assertEqual(self.expired_project.payout_status, None)
        self.assertEqual(self.expired_project.status, self.complete)


class TestProjectPhaseLog(BluebottleTestCase):
    def setUp(self):
        super(TestProjectPhaseLog, self).setUp()
        self.init_projects()

    def test_create_phase_log(self):
        phase1 = ProjectPhaseFactory.create()
        phase2 = ProjectPhaseFactory.create()

        project = ProjectFactory.create(status=phase1)

        phase_logs = ProjectPhaseLog.objects.all()
        self.assertEquals(len(phase_logs), 1)
        self.assertEquals(phase_logs[0].status, project.status)

        project.status = phase2
        project.save()

        phase_logs = ProjectPhaseLog.objects.all().order_by("-start")
        self.assertEquals(len(phase_logs), 2)
        self.assertEquals(phase_logs[0].status, project.status)


class SupporterCountTest(BluebottleTestCase):
    def setUp(self):
        super(SupporterCountTest, self).setUp()

        # Required by Project model save method
        self.init_projects()

        self.some_project = ProjectFactory.create(amount_asked=5000)
        self.another_project = ProjectFactory.create(amount_asked=5000)

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

    def test_supporter_count_new(self):
        self.assertEqual(self.some_project.supporter_count(), 0)

        self._create_donation(user=self.some_user, status=StatusDefinition.NEW)

        self.assertEqual(self.some_project.supporter_count(), 0)

    def test_supporter_count_success(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_pending(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.PENDING)

        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_unique(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 1)

        self._create_donation(user=self.another_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 2)

    def test_supporter_count_anonymous(self):
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_anonymous_not_unique(self):
        self._create_donation(status=StatusDefinition.SUCCESS)
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 2)

    def test_supporter_count_anonymous_and_user(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self._create_donation(user=self.another_user,
                              status=StatusDefinition.SUCCESS)

        self._create_donation(status=StatusDefinition.SUCCESS)
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 4)

    def _create_donation(self, user=None, status=StatusDefinition.NEW):
        """ Helper method for creating donations."""
        order = Order.objects.create(status=status, user=user)
        donation = Donation.objects.create(amount=100,
                                           project=self.some_project,
                                           order=order)

        return donation


class TestProjectStatusChangeSuggestionUpdate(BluebottleTestCase):
    def setUp(self):
        super(TestProjectStatusChangeSuggestionUpdate, self).setUp()

        self.init_projects()

        self.new = ProjectPhase.objects.get(slug="plan-new")
        self.needs_work = ProjectPhase.objects.get(slug="plan-needs-work")
        self.submitted = ProjectPhase.objects.get(slug="plan-submitted")

    def test_project_submitted_suggestion_submitted(self):
        """
        Test that suggestion has status submitted if a project status
        changes to submitted
        """
        project = ProjectFactory.create(status=self.new)
        suggestion = SuggestionFactory.create(project=project,
                                              token='xxx',
                                              status='in_progress')

        project.status = self.submitted
        project.save()

        suggestion = Suggestion.objects.get(project=project)

        self.assertEquals(suggestion.status, 'submitted')

    def test_project_needs_work_suggestion_in_progress(self):
        """
        Test that suggestion has status in-progress if a project status
        changes to needs-work
        """
        project = ProjectFactory.create(status=self.submitted)
        suggestion = SuggestionFactory.create(project=project,
                                              token='xxx',
                                              status='submitted')

        project.status = self.needs_work
        project.save()

        suggestion = Suggestion.objects.get(project=project)

        self.assertEquals(suggestion.status, 'in_progress')


class TestProjectPopularity(BluebottleTestCase):
    def setUp(self):
        super(TestProjectPopularity, self).setUp()
        self.init_projects()

        self.project = ProjectFactory.create()

        VoteFactory.create(project=self.project)
        task = TaskFactory.create(project=self.project)
        TaskMemberFactory.create(task=task)

        order = OrderFactory.create(status=StatusDefinition.SUCCESS)

        DonationFactory(order=order, project=self.project)

    def test_update_popularity(self):
        Project.update_popularity()

        self.assertEqual(Project.objects.get(id=self.project.id).popularity, 11)


class TestProjectBulkActions(BluebottleTestCase):
    def setUp(self):
        super(TestProjectBulkActions, self).setUp()
        self.init_projects()

        self.projects = [ProjectFactory.create(title='test {}'.format(i)) for i in range(10)]
        self.request = RequestFactory().post('/admin/some', data={'action': 'plan-new'})

    def test_mark_as_plan_new(self):
        mark_as(None, self.request, Project.objects)

        for project in Project.objects.all():
            self.assertEqual(project.status.slug, 'plan-new')

    def test_project_phase_log_creation(self):
        mark_as(None, self.request, Project.objects)

        for project in Project.objects.all():
            log = ProjectPhaseLog.objects.filter(project=project).order_by('start').last()
            self.assertEqual(log.status.slug, 'plan-new')

    def test_mark_annotated(self):
        queryset = Project.objects.annotate(
            admin_vote_count=Count('vote', distinct=True)
        )
        mark_as(None, self.request, queryset)

        for project in Project.objects.all():
            self.assertEqual(project.status.slug, 'plan-new')


class TestProjectUpdateAmounts(BluebottleTestCase):
    def setUp(self):
        super(TestProjectUpdateAmounts, self).setUp()
        self.init_projects()

        self.project = ProjectFactory.create(title='test')

    def test_total_no_donations(self):
        self.project.update_amounts()
        self.assertEqual(self.project.amount_donated.amount, 0)
        self.assertEqual(self.project.amount_needed, self.project.amount_asked)
        self.assertEqual(self.project.amount_donated.currency, self.project.amount_asked.currency)

    def test_total_multi_currency(self):
        order1 = OrderFactory.create(status=StatusDefinition.SUCCESS)
        order2 = OrderFactory.create(status=StatusDefinition.SUCCESS)

        for i in range(100, 401, 100):
            DonationFactory.create(
                project=self.project,
                order=order1,
                amount=Money(i, 'EUR'),
            )
            DonationFactory.create(
                project=self.project,
                order=order2,
                amount=Money(i, 'USD'),
            )

        self.project.update_amounts()
        self.assertEqual(self.project.amount_donated.amount, 2500)
        self.assertEqual(self.project.amount_needed.amount, self.project.amount_asked.amount - 2500)
        self.assertEqual(self.project.amount_donated.currency, self.project.amount_asked.currency)

    def test_change_amount_asked_currency(self):
        new_amount = Money(1000, 'USD')
        self.project.amount_asked = new_amount
        self.project.save()

        self.assertEqual(self.project.amount_asked.currency, new_amount.currency)
        self.assertEqual(self.project.amount_extra.currency, new_amount.currency)
        self.assertEqual(self.project.amount_donated.currency, new_amount.currency)


class TestModel(BluebottleTestCase):
    def setUp(self):
        super(TestModel, self).setUp()

        self.init_projects()
        self.project = ProjectFactory.create()

    def test_expertise_based(self):
        skill = SkillFactory.create(expertise=True)
        TaskFactory.create(skill=skill, project=self.project)

        self.assertTrue(self.project.expertise_based)

    def test_expertise_based_no_task(self):
        self.assertFalse(self.project.expertise_based)

    def test_expertise_based_no_expertise(self):
        skill = SkillFactory.create(expertise=False)
        TaskFactory.create(skill=skill, project=self.project)

        self.assertFalse(self.project.expertise_based)

    def test_donated_percentage(self):
        self.project.amount_asked = Money(0, 'EUR')
        self.assertEqual(self.project.donated_percentage, 0)
        self.project.amount_asked = Money(20, 'EUR')
        self.project.amount_donated = Money(40, 'EUR')
        self.assertEqual(self.project.donated_percentage, 100)
        self.project.amount_asked = Money(20, 'EUR')
        self.project.amount_donated = Money(10, 'EUR')
        self.assertEqual(self.project.donated_percentage, 50)


class TestProjectTheme(BluebottleTestCase):
    def setUp(self):
        super(TestProjectTheme, self).setUp()

        self.init_projects()
        self.theme = ProjectThemeFactory.create()
        self.project = ProjectFactory.create(theme=self.theme)

    def test_removing_theme_should_not_remove_project(self):
        """
        Removing the theme should not cascade and remove project.
        """
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())
        self.theme.delete()
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())


class TestProjectBudgetLine(BluebottleTestCase):
    def setUp(self):
        super(TestProjectBudgetLine, self).setUp()
        self.init_projects()
        self.project = ProjectFactory.create()

    def test_project_budget_line(self):
        line = ProjectBudgetLine.objects.create(
            project=self.project,
            description='Just things',
            amount=Money(50, 'EUR')
        )
        line.save()
        self.assertEqual(unicode(line), u'Just things - 50.00 \u20ac')


class TestProjectPlatformSettings(BluebottleTestCase):

    def test_load_new_settings(self):
        settings = ProjectPlatformSettings.load()
        self.assertEqual(settings.allow_anonymous_rewards, True)

    def test_load_existing_settings(self):
        ProjectPlatformSettings.objects.create(allow_anonymous_rewards=False)
        settings = ProjectPlatformSettings.load()
        self.assertEqual(settings.allow_anonymous_rewards, False)

    def test_extra_project_fields(self):
        project = ProjectFactory.create()
        custom = CustomProjectFieldSettings.objects.create(name='Extra Info')

        # Check that the slug is set correctly
        self.assertEqual(custom.slug, 'extra-info')

        # Check that the project doesn't have extra field yet
        project.refresh_from_db()
        self.assertEqual(project.extra.count(), 0)

        CustomProjectField.objects.create(project=project, value='This is nice!', field=custom)

        # And now it should be there
        project.refresh_from_db()
        self.assertEqual(project.extra.count(), 1)


@override_settings(MAPS_API_KEY='somekey')
class TestProjectLocation(BluebottleTestCase):
    def setUp(self):
        self.project = ProjectFactory.create(language=Language.objects.get(code='en'))
        self.location = ProjectLocation(
            project=self.project,
            latitude=52.3721249,
            longitude=4.9070198
        )
        self.mock_result = {
            'results': [{
                'geometry': {
                    'location': {'lat': 52.3721249, 'lng': 4.9070198},
                    'viewport': {
                        'northeast': {'lat': 52.37347388029149, 'lng': 4.908368780291502},
                        'southwest': {'lat': 52.37077591970849, 'lng': 4.905670819708497}
                    },
                    'location_type': 'ROOFTOP'
                },
                'place_id': u'ChIJMW3CZ7sJxkcRyhrLgJ6WbMk',
                'address_components': [{
                    'long_name': '10', 'types': ['street_number'], 'short_name': '10'
                }, {
                    'long_name': "'s-Gravenhekje", 'types': ['route'], 'short_name': "'s-Gravenhekje"
                }, {
                    'long_name': 'Amsterdam-Centrum',
                    'types': ['political', 'sublocality', 'sublocality_level_1'],
                    'short_name': 'Amsterdam-Centrum'
                }, {
                    'long_name': u'Amsterdam',
                    'types': ['locality', 'political'], 'short_name': 'Amsterdam'
                }, {
                    'long_name': 'Amsterdam',
                    'types': ['administrative_area_level_2', 'political'],
                    'short_name': 'Amsterdam'
                }, {
                    'long_name': 'Noord-Holland',
                    'types': ['administrative_area_level_1', 'political'],
                    'short_name': u'NH'
                }, {
                    'long_name': 'Netherlands',
                    'types': [u'country', u'political'],
                    'short_name': u'NL'
                }, {
                    'long_name': '1011 TG', 'types': [u'postal_code'], 'short_name': u'1011 TG'
                }],
                'types': ['street_address'],
            }],
            'status': 'OK'
        }

    @property
    def geocode_mock_factory(self):
        @httmock.urlmatch(netloc='maps.googleapis.com')
        def geocode_mock(url, request):
            self.assertEqual(
                urlparse.parse_qs(url.query)['language'][0], self.project.language.code
            )
            return json.dumps(self.mock_result)

        return geocode_mock

    def save_location(self):
        with httmock.HTTMock(self.geocode_mock_factory):
            self.location.save()

    def test_adjusting_geolocation(self):
        self.location.latitude = 52.166315
        self.location.longitude = 4.490936
        self.location.save()
        self.location.latitude = 43.059269
        self.location.longitude = 23.681429
        self.location.save()

    def test_geocode(self):
        self.save_location()
        self.assertEqual(
            self.location.street, "'s-Gravenhekje"
        )
        self.assertEqual(
            self.location.country, "Netherlands"
        )
        self.assertEqual(
            self.location.neighborhood, "Amsterdam-Centrum"
        )
        self.assertEqual(
            self.location.city, "Amsterdam"
        )

    def test_geocode_different_langauge(self):
        self.project.language = Language.objects.get(code='nl')
        self.save_location()
        self.assertEqual(
            self.location.street, "'s-Gravenhekje"
        )

    @override_settings(MAPS_API_KEY=None)
    def test_geocode_no_key(self):
        self.save_location()
        self.assertEqual(
            self.location.street, None
        )

    def test_geocode_unnamed_street(self):
        self.mock_result['results'][0]['address_components'][1]['long_name'] = 'Unnamed Road'
        self.save_location()
        self.assertEqual(
            self.location.street, None
        )
