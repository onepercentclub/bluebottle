from django.utils.translation import ugettext as _

from djchoices import DjangoChoices, ChoiceItem


class PayoutLineStatuses(DjangoChoices):
    """ Status options for payouts. """
    new = ChoiceItem('new', label=_("New"))
    progress = ChoiceItem('progress', label=_("Progress"))
    completed = ChoiceItem('completed', label=_("Completed"))
