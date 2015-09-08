"""

NOTE:
Mail system moved to each app that needs to implement it.
get a look at notifiers.py



The prescribed mail flow is as follows:

1) Wallposts created

    a) send email to Object owner, if Wallpost author is not the Object owner
       (except if he already got an email via 2c).

2) Reaction created on Wallpost

    a) send email to Object owner, if Reaction author is not the Object ower.
    b) send email to Wallpost author, if Reaction author is not the
       Wallpost author.
    c) send email to other Reaction authors that are not the Object owner or
       the Wallpost author (they already get an
       email, see above).

Example::

    Object by A
    |
    +-- Wallpost by B
        |
        +-- Reaction by C


Basically, everyone in the tree gets an email if a new Wallpost or Reaction
is created, except the author if the newly created Wallpost or Reaction.
But, every unique person shall receive at most 1 email.

"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.utils.model_dispatcher import get_project_model, get_task_model
from bluebottle.wallposts.models import Reaction, TextWallpost
from bluebottle.wallposts.notifiers import ObserversContainer


# NOTE
# The following two calls (TASK_MODEL, PROJECT_MODEL )are needed for no
# clear reason...
# if you take them out you will receive the following error message:
# ===========
# django.core.management.base.CommandError: One or more models did not validate:
# vouchers.voucher: 'order' has a relation with model fund.Order, which has
# either not been installed or is abstract. cowry.payment: 'order' has a
# relation with model fund.Order, which has either not been installed
# or is abstract.
# ===========
TASK_MODEL = get_task_model()
PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)


@receiver(post_save, weak=False, sender=TextWallpost)
def new_wallpost_notification(sender, instance, created, **kwargs):
    container = ObserversContainer()
    container.notify_wallpost_observers(instance)


@receiver(post_save, weak=False, sender=Reaction)
def new_reaction_notification(sender, instance, created, **kwargs):
    container = ObserversContainer()
    container.notify_reaction_observers(instance)
