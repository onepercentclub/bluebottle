from django.conf import settings
from django.db import models
from bluebottle.bb_projects.models import BaseProject, BaseProjectPhaseLog
from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.bb_organizations.models import BaseOrganization, BaseOrganizationMember, BaseOrganizationDocument
from bluebottle.bb_tasks.models import BaseTask, BaseSkill, BaseTaskFile, BaseTaskMember
from bluebottle.utils.models import Address

class TestBaseProjectPhaseLog(BaseProjectPhaseLog):
    """
    Instantiate default BaseProjectPhaseLog abstract class
    """
    pass


class TestBaseProject(BaseProject):
    """
    Instantiate the abstract base model for a project. Used only for testing.
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


class TestSkill(BaseSkill):
    """
    Implementation for testing of BaseSkill
    """
    pass


class TestTaskMember(BaseTaskMember):
    """
    Implementation for testing of BaseMember
    """
    pass


class TestTaskFile(BaseTaskFile):
    """
    Implementation for testing of BaseTaskFile
    """
    pass


class TestOrganizationMember(BaseOrganizationMember):
    """
    Implementation for testing of BaseOrganizationMember
    """
    pass


class TestOrganizationDocument(BaseOrganizationDocument):
    """
    Implementation for testing of BaseOrganizationDocument
    """
    pass


class TestAddress(Address):
    """
    A postal address.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="address")
