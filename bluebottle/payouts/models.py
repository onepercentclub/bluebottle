from bluebottle.bb_payouts.models import BaseProjectPayout, BaseOrganizationPayout
from bluebottle.utils.model_dispatcher import get_project_model

PROJECT_MODEL = get_project_model()


class ProjectPayout(BaseProjectPayout):
    pass


class OrganizationPayout(BaseOrganizationPayout):
    pass

