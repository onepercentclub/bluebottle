from bluebottle.bb_projects.models import BaseProject
from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.bb_organizations.models import BaseOrganization
from bluebottle.bb_tasks.models import BaseTask


class TestBaseProject(BaseProject):
    """
    Instantiate the abstract base model for a user with no additional attributes. Used only for testing.
    """
    pass


class TestBaseUser(BlueBottleBaseUser):
    """
    Instantiate the abstract base model for a user with no additional
    attributes. Used only for testing.
    """
    pass


class TestOrganization(BaseOrganization):
    """
    Instantiation of abstract BaseOrganization. Used only for testing.
    """
    pass


class TestTask(BaseTask):
    """
    Implementation of BaseTask. Used only for testing purposes.
    """
    pass