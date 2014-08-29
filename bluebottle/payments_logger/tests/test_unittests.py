from django.test import TestCase
from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model

PROJECT_MODEL = get_project_model()
PROJECT_PHASE_LOG_MODEL = get_project_phaselog_model()

class TestPaymentLogger(TestCase):

    def test_create_payment_log(self):

        phase1 = ProjectPhaseFactory.create()
        phase2 = ProjectPhaseFactory.create()