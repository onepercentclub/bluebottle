from bluebottle.bb_organizations.models import BaseOrganization


class TestOrganization(BaseOrganization):
    """
    Instantiation of abstract BaseOrganization. Used only for testing.
    """
    pass

from .test_api import *
# from .test_unittests import *