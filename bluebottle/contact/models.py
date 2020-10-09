from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import CreationDateTimeField, \
    ModificationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible

from .mails import send_contact_email
from bluebottle.clients import properties


@python_2_unicode_compatible
class ContactMessage(models.Model):
    """
    Message sent from Contact Page
    """

    class ContactStatus(DjangoChoices):
        new = ChoiceItem('new', label=_("New"))
        in_progress = ChoiceItem('in progress', label=_("In progress"))
        closed = ChoiceItem('closed', label=_("Closed"))

    status = models.CharField(_('status'), max_length=20,
                              choices=ContactStatus.choices,
                              default=ContactStatus.new)

    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('author'), blank=True, null=True)
    name = models.CharField(_("Name"), max_length=200)
    email = models.EmailField(_("Email"), max_length=200)
    message = models.TextField(_("Message"))

    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    def __str__(self):
        return self.message[0:30]


def mail_contact_message(sender, instance, **kwargs):
    """ Send an e-mail with the contact message content """
    if kwargs['created']:
        send_contact_email(instance, properties.CONTACT_EMAIL)


post_save.connect(mail_contact_message, sender=ContactMessage)
