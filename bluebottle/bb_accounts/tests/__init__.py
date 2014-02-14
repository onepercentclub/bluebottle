from bluebottle.bb_accounts.models import BlueBottleBaseUser


class TestBaseUser(BlueBottleBaseUser):
    """
    Instantiate the abstract base model for a user with no additional
    attributes. Used only for testing.
    """
    pass

from .test_models import *
# from .unittests import *
