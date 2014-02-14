from bluebottle.bb_tasks.models import BaseTask


class TestTask(BaseTask):
    """
    Implementation of BaseTask. Used only for testing purposes.
    """
    pass


from .test_api import *
from .test_mails import *
from . test_unittests import *

