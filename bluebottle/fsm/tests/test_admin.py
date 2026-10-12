from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory

from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.initiatives.admin import InitiativeAdmin
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class StateMachineAdminFormTestCase(BluebottleTestCase):
    """
    The transitions offered in the admin are checked against the permissions
    of the user making the request. Approving an initiative requires staff.
    """

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status='submitted')
        self.model_admin = InitiativeAdmin(Initiative, AdminSite())

    def get_transitions(self, user):
        request = RequestFactory().get('/')
        request.user = user
        form_class = self.model_admin.get_form(request, self.initiative)
        form = form_class(instance=self.initiative)
        return [transition.field for _, transition in form.fields['states'].choices]

    def test_staff_user(self):
        transitions = self.get_transitions(BlueBottleUserFactory.create(is_staff=True))
        self.assertIn('approve', transitions)

    def test_user_without_permission(self):
        transitions = self.get_transitions(BlueBottleUserFactory.create(is_staff=False))
        self.assertNotIn('approve', transitions)

    def test_form_sets_user(self):
        user = BlueBottleUserFactory.create(is_staff=True)
        request = RequestFactory().get('/')
        request.user = user
        form_class = self.model_admin.get_form(request, self.initiative)
        self.assertTrue(issubclass(form_class, StateMachineModelForm))
        self.assertEqual(form_class.user, user)

    def test_form_without_user(self):
        # Forms built outside StateMachineAdminMixin.get_form (e.g. inlines) have
        # no user and keep offering all transitions, like before
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create(is_staff=True)
        form_class = self.model_admin.get_form(request, self.initiative)
        form_class.user = None
        form = form_class(instance=self.initiative)
        transitions = [transition.field for _, transition in form.fields['states'].choices]
        self.assertIn('approve', transitions)
