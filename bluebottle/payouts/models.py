#from bluebottle.bb_payouts.models import BaseProjectPayout, BaseOrganizationPayout
from bluebottle.bb_payouts.models import PayoutBase, BaseProjectPayout, BaseOrganizationPayout


class ProjectPayout(BaseProjectPayout):
    pass


class OrganizationPayout(BaseOrganizationPayout):
    pass