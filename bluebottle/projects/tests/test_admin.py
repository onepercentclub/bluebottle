# -*- coding: utf-8 -*-
import csv
import json
import mock
from moneyed import Money
import StringIO
import requests

from django.db import connection
from django.contrib.admin.sites import AdminSite
from django.contrib import messages
from django.forms.models import modelform_factory
from django.test.client import RequestFactory
from django.urls.base import reverse
from django.utils.timezone import now


from bluebottle.projects.admin import (
    LocationFilter, ProjectReviewerFilter, ProjectAdminForm,
    ReviewerWidget, ProjectAdmin)
from bluebottle.projects.models import Project, ProjectPhase, CustomProjectFieldSettings, CustomProjectField
from bluebottle.projects.tasks import refund_project
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.utils import BluebottleTestCase, override_settings, BluebottleAdminTestCase


factory = RequestFactory()


PAYOUT_URL = 'http://localhost:8001/payouts/update/'


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None, is_staff=True):
        self.perms = perms or []
        self.is_staff = is_staff

    def has_perm(self, perm):
        return perm in self.perms


@override_settings(PAYOUT_SERVICE={
    'service': 'dorado',
    'url': PAYOUT_URL
})
class TestProjectAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAdmin, self).setUp()
        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.init_projects()
        self.project_admin = ProjectAdmin(Project, self.site)
        self.mock_response = requests.Response()
        self.mock_response.status_code = 200
        self.status_done = ProjectPhase.objects.get(slug='done-complete')
        self.status_campaign = ProjectPhase.objects.get(slug='campaign')

    def _generate_completed_project(self):
        project = ProjectFactory.create(amount_asked=Money(100, 'EUR'),
                                        status=self.status_campaign,
                                        deadline=now())
        donation = DonationFactory.create(
            project=project,
            amount=100
        )
        donation.save()
        donation.order.locked()
        donation.order.success()
        donation.order.save()
        project.save()
        project.deadline_reached()
        return project

    def test_sourcing_fieldsets(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])
        project = ProjectFactory.create(project_type='sourcing')
        self.assertEqual(len(self.project_admin.get_fieldsets(request, project)), 3)

    def test_payout_status(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])
        project = ProjectFactory.create(project_type='funding')
        self.assertIn('payout_status', self.project_admin.get_fieldsets(request, project)[3][1]['fields'])

    def test_search_fields(self):
        self.assertIn('organization__contacts__email', self.project_admin.search_fields)

    def test_amount_needed(self):
        project = ProjectFactory(amount_asked=Money(100, 'EUR'))
        self.assertEqual(
            self.project_admin.amount_needed_i18n(project),
            Money(100, 'EUR')
        )

    def test_amount_needed_with_extra(self):
        project = ProjectFactory(amount_asked=Money(100, 'EUR'), amount_extra=Money(50, 'EUR'))
        self.assertEqual(
            self.project_admin.amount_needed_i18n(project),
            Money(50, 'EUR')
        )

    def test_amount_needed_with_more_extra(self):
        project = ProjectFactory(amount_asked=Money(100, 'EUR'), amount_extra=Money(150, 'EUR'))
        self.assertEqual(
            self.project_admin.amount_needed_i18n(project),
            Money(0, 'EUR')
        )

    def test_fieldsets_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_fieldsets(request)
        )

    def test_list_filter(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertIn('payout_status', self.project_admin.get_list_filter(request))
        self.assertIn('categories', self.project_admin.get_list_filter(request))

    def test_list_filter_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_filter(request)
        )

    def test_list_filter_task_skills(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'skill' not in self.project_admin.get_list_filter(request)
        )

    def test_list_display(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_display(request)
        )

    def test_list_display_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_display(request)
        )

    def test_mark_payout_as_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = 'NL86 INGB 0002 4455 88'
        project.account_details = 'INGBNL2A'
        project.save()

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        # Check that IBAN has spaces removed
        project = Project.objects.get(pk=project.id)
        self.assertEqual(project.account_number, 'NL86INGB0002445588')

    def test_mark_payout_as_approved_remote_validation_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = '123456123456'
        project.save()

        self.mock_response.status_code = 400
        self.mock_response._content = json.dumps({'errors': {'name': ['This field is required']}})
        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)
        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Account details: name, this field is required.', level=messages.ERROR
        )

    def test_mark_payout_as_approved_local_iban_validation_error(self):
        # Test with invalid IBAN, but starting with letter
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = 'HH239876'
        project.account_details = 'RABONL2U'
        project.save()

        with mock.patch.object(self.project_admin, 'message_user') as message_mock:
            self.project_admin.approve_payout(request, project.id)
        message_mock.assert_called_with(
            request, "Invalid IBAN: Unknown country-code 'HH'", level='ERROR'
        )

    def test_mark_payout_as_approved_local_validation_error(self):
        # Test with valid IBAN and invalid BIC
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = 'NL86 INGB 0002 4455 88'
        project.account_details = 'Amsterdam'
        project.save()

        with mock.patch.object(self.project_admin, 'message_user') as message_mock:
            self.project_admin.approve_payout(request, project.id)
        message_mock.assert_called_with(
            request, "Invalid BIC: Invalid length '9'", level='ERROR'
        )

    def test_mark_payout_as_approved_internal_server_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = '123456123456'
        project.save()

        self.mock_response.status_code = 500
        self.mock_response._content = 'Internal Server Error'

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Failed to approve payout: Internal Server Error', level=messages.ERROR
        )

    def test_mark_payout_as_approved_connection_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = '123456123456'
        project.save()

        exception = requests.ConnectionError('Host not found')

        with mock.patch('requests.post', side_effect=exception) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Failed to approve payout: Host not found', level=messages.ERROR
        )

    def test_mark_payout_as_approved_no_permissions(self):
        request = self.request_factory.post('/')
        request.user = MockUser()

        project = ProjectFactory.create(payout_status='needs_approval')
        project.account_number = '123456123456'
        project.save()

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                response = self.project_admin.approve_payout(request, project.id)

        self.assertEqual(response.status_code, 302)
        request_mock.assert_not_called()
        message_mock.assert_called_with(
            request, 'Missing permission: projects.approve_payout', level='ERROR'
        )

    def test_mark_payout_as_approved_wrong_status(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = '123456123456'
        project.payout_status = 'done'
        project.save()

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'done'
        )
        request_mock.assert_not_called()
        message_mock.assert_called()

    def test_read_only_status_after_payout_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = self._generate_completed_project()
        project.account_number = '123456123456'
        project.save()

        # Project status should be editable
        self.assertFalse(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )

        def side_effect(*args, **kwargs):
            project.payout_status = 'approved'
            project.save()
            return self.mock_response

        with mock.patch('requests.post', side_effect=side_effect):
            self.project_admin.approve_payout(request, project.id)

        project = Project.objects.get(id=project.id)

        # Project status should be readonly after payout has been approved
        self.assertTrue(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )

    def test_export_rewards(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        project = ProjectFactory.create(title="¡Tést, with löt's of weird things!")
        reward = RewardFactory.create(project=project, amount=Money(10, 'EUR'))

        reward_order = OrderFactory.create(status='success')
        donation = DonationFactory.create(
            project=project,
            reward=reward,
            order=reward_order,
            amount=Money(100, 'EUR')
        )

        order = OrderFactory.create(status='success')
        DonationFactory.create(project=project, order=order)

        response = self.project_admin.export_rewards(request, project.id)
        header = 'Content-Type: text/csv\r\n' \
                 'Content-Disposition: attachment; ' \
                 'filename="test-with-lots-of-weird-things.csv"'
        self.assertEqual(response.serialize_headers(), header)

        reader = csv.DictReader(StringIO.StringIO(response.content))

        result = [line for line in reader]
        self.assertEqual(len(result), 1)
        line = result[0]

        self.assertEqual(line['Email'], reward_order.user.email)
        self.assertEqual(line['Name'], reward_order.user.full_name)
        self.assertEqual(line['Order id'], str(reward_order.id))
        self.assertEqual(line['Reward'], reward.title)
        self.assertEqual(line['Description'], reward.description)
        self.assertEqual(line['Amount'], str(reward.amount))
        self.assertEqual(line['Actual Amount'], str(donation.amount))

    def test_export_rewards_anonymous(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        project = ProjectFactory.create()
        reward = RewardFactory.create(project=project, amount=Money(10, 'EUR'))

        reward_order = OrderFactory.create(status='success', user=None)
        donation = DonationFactory.create(
            project=project,
            reward=reward,
            order=reward_order,
            name='test',
            amount=Money(100, 'EUR')
        )

        order = OrderFactory.create(status='success')
        DonationFactory.create(project=project, order=order)

        response = self.project_admin.export_rewards(request, project.id)
        reader = csv.DictReader(StringIO.StringIO(response.content))

        result = [line for line in reader]
        self.assertEqual(len(result), 1)
        line = result[0]

        self.assertEqual(line['Email'], '')
        self.assertEqual(line['Name'], '')
        self.assertEqual(line['Order id'], str(reward_order.id))
        self.assertEqual(line['Reward'], reward.title)
        self.assertEqual(line['Amount'], str(reward.amount))
        self.assertEqual(line['Actual Amount'], str(donation.amount))
        self.assertEqual(line['Name on Donation'], donation.name)

    def test_export_rewards_forbidden(self):
        request = self.request_factory.get('/')
        request.user = MockUser(is_staff=False)

        project = ProjectFactory.create()
        response = self.project_admin.export_rewards(request, project.id)

        self.assertEqual(response.status_code, 403)


@override_settings(ENABLE_REFUNDS=True)
class TestProjectRefundAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestProjectRefundAdmin, self).setUp()
        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.init_projects()
        self.project_admin = ProjectAdmin(Project, self.site)

        self.project = ProjectFactory.create(
            status=ProjectPhase.objects.get(slug='closed'),
        )

        self.order = OrderFactory.create(
            status='success'
        )

        DonationFactory.create(
            project=self.project,
            order=self.order,
            amount=Money(100, 'EUR'),
        )

        self.request = self.request_factory.post('/')
        self.request.user = MockUser(['payments.refund_orderpayment'])

    def test_refunds(self):
        with mock.patch.object(refund_project, 'delay') as refund_mock:
            response = self.project_admin.refund(self.request, self.project.pk)

            self.assertEqual(response.status_code, 302)

            refund_mock.assert_called_with(connection.tenant, self.project)

    @override_settings(ENABLE_REFUNDS=True)
    def test_refunds_not_closed(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        with mock.patch.object(refund_project, 'delay') as refund_mock:
            response = self.project_admin.refund(self.request, self.project.pk)

            self.assertEqual(response.status_code, 403)
            refund_mock.assert_not_called()

    @override_settings(ENABLE_REFUNDS=True)
    def test_refunds_no_amount(self):
        self.order.transition_to('failed')
        self.order.save()

        with mock.patch.object(refund_project, 'delay') as refund_mock:
            response = self.project_admin.refund(self.request, self.project.pk)

            self.assertEqual(response.status_code, 403)
            refund_mock.assert_not_called()

    @override_settings(ENABLE_REFUNDS=True)
    def test_refunds_no_permission(self):
        self.request.user.perms = []

        with mock.patch.object(refund_project, 'delay') as refund_mock:
            response = self.project_admin.refund(self.request, self.project.pk)
            self.assertEqual(response.status_code, 403)
            refund_mock.assert_not_called()

    @override_settings(ENABLE_REFUNDS=False)
    def test_refunds_disabled(self):
        with mock.patch.object(refund_project, 'delay') as refund_mock:
            response = self.project_admin.refund(self.request, self.project.pk)

            self.assertEqual(response.status_code, 403)
            refund_mock.assert_not_called()


class LocationFilterTest(BluebottleTestCase):
    """
    Test project admin location filter
    """

    def setUp(self):
        super(LocationFilterTest, self).setUp()
        self.init_projects()

        amsterdam = LocationFactory.create(name='Amsterdam')
        rotterdam = LocationFactory.create(name='Rotterdam')
        durgerdam = LocationFactory.create(name='Durgerdam')
        self.locations = [amsterdam, rotterdam, durgerdam]

        self.user = BlueBottleUserFactory.create(location=amsterdam)
        self.amsterdam_project = ProjectFactory.create(
            title='Project in Amsterdam',
            location=amsterdam
        )
        ProjectFactory.create(
            title='Project in Rotterdam',
            location=rotterdam
        )
        ProjectFactory.create(
            title='Project in Durgerdam',
            location=durgerdam
        )
        self.admin = ProjectAdmin(Project, AdminSite())

        self.filter = LocationFilter(None, {'location': amsterdam.pk}, Project, self.admin)

    def testLookup(self):
        request = factory.get('/', user=None)

        lookups = self.filter.lookups(request, self.admin)
        self.assertEqual(
            set(location.name for location in self.locations),
            set(lookup[1] for lookup in lookups)
        )

    def testLookupUser(self):
        request = factory.get('/')
        request.user = self.user
        lookups = self.filter.lookups(request, self.admin)

        self.assertEqual(len(lookups), 4)
        self.assertEqual(
            lookups[0],
            (request.user.location.id, u'My location (Amsterdam)')
        )

    def test_filter(self):
        queryset = self.filter.queryset(None, Project.objects.all())
        self.assertEqual(queryset.get(), self.amsterdam_project)


class ProjectReviewerFilterTest(BluebottleTestCase):
    """
    Test project reviewer filter
    """

    def setUp(self):
        super(ProjectReviewerFilterTest, self).setUp()
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.project_with_reviewer = ProjectFactory.create(
            reviewer=self.user
        )
        self.project = ProjectFactory.create(
        )

        self.request = factory.get('/')
        self.request.user = self.user
        self.admin = ProjectAdmin(Project, AdminSite())

    def test_filter(self):
        filter = ProjectReviewerFilter(None, {'reviewer': True}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(queryset.get(), self.project_with_reviewer)

    def test_filter_false(self):
        filter = ProjectReviewerFilter(None, {'reviewer': False}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(len(queryset), len(Project.objects.all()))


class ProjectAdminFormTest(BluebottleTestCase):
    def setUp(self):
        super(ProjectAdminFormTest, self).setUp()
        self.init_projects()
        self.form = modelform_factory(Project, ProjectAdminForm, exclude=[])()

    def test_reviewer_field(self):
        widget = self.form.fields['reviewer'].widget
        self.assertTrue(
            isinstance(widget, ReviewerWidget)
        )
        parameters = widget.url_parameters()
        self.assertTrue(parameters['is_staff'], True)


class ProjectCustomFieldAdminTest(BluebottleAdminTestCase):
    """
    Test extra fields in Project Admin
    """

    def setUp(self):
        super(ProjectCustomFieldAdminTest, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()

    def test_custom_fields(self):
        project = ProjectFactory.create(title='Test')
        field = CustomProjectFieldSettings.objects.create(name='How is it')
        project.extra.create(value='This is nice!', field=field)
        project.save()

        project_url = reverse('admin:projects_project_change', args=(project.id, ))
        response = self.client.get(project_url)
        self.assertEqual(response.status_code, 200)
        # Test the extra field and it's value show up
        self.assertContains(response, 'How is it')
        self.assertContains(response, 'This is nice!')

    def test_save_custom_fields(self):
        project = ProjectFactory.create(title='Test')
        CustomProjectFieldSettings.objects.create(name='Purpose')

        data = project.__dict__
        # Set some foreignkeys and money fields
        # TODO: There should be a more elegant solution for this.
        data['status'] = 1
        data['theme'] = 1
        data['owner'] = 1
        data['amount_extra_0'] = 100.0
        data['amount_extra_1'] = 'EUR'
        data['amount_needed_0'] = 100.0
        data['amount_needed_1'] = 'EUR'
        data['amount_asked_0'] = 100.0
        data['amount_asked_1'] = 'EUR'
        data['amount_donated_0'] = 0.0
        data['amount_donated_1'] = 'EUR'

        # Set the extra field
        data['purpose'] = 'Do good better'
        form = ProjectAdminForm(instance=project, data=data)
        self.assertEqual(form.errors, {})
        form.save()
        project.refresh_from_db()
        self.assertEqual(project.extra.get().value, 'Do good better')


class ProjectAdminExportTest(BluebottleTestCase):
    """
    Test csv export
    """
    def setUp(self):
        super(ProjectAdminExportTest, self).setUp()
        self.init_projects()
        self.request_factory = RequestFactory()
        self.request = self.request_factory.post('/')
        self.request.user = MockUser()
        self.init_projects()
        self.project_admin = ProjectAdmin(Project, AdminSite())

    def test_project_export(self):
        project = ProjectFactory(title='Just an example')
        CustomProjectFieldSettings.objects.create(name='Extra Info')
        field = CustomProjectFieldSettings.objects.create(name='How is it')
        CustomProjectField.objects.create(project=project, value='This is nice!', field=field)

        export_action = self.project_admin.actions[0]
        response = export_action(self.project_admin, self.request, self.project_admin.get_queryset(self.request))

        data = response.content.split("\r\n")
        headers = data[0].split(",")
        data = data[1].split(",")

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers[0], 'title')
        self.assertEqual(headers[28], 'Extra Info')
        self.assertEqual(data[0], 'Just an example')
        self.assertEqual(data[28], '')
        self.assertEqual(data[29], 'This is nice!')
