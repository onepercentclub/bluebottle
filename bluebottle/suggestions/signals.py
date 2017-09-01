from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.suggestions.models import Suggestion
from bluebottle.utils.email_backend import send_mail


class User(dict):
    pass


@receiver(post_save, weak=False, sender=Suggestion,
          dispatch_uid='suggestion_model')
def send_suggestion_confirmation_email(sender, instance,
                                       created, **kwargs):
    """ Send a confirmation email when a new Suggestion is created """
    if created:

        with TenantLanguage(instance.language):
            subject = _('Thank you for submitting your project request.')

        url = getattr(properties, 'OPEN_EXTERNAL_URL', None)

        if not url:
            return

        tokenurl = '{0}/confirm-suggestion/{1}/{2}'.format(url,
                                                           instance.token,
                                                           instance.language)

        user = User()
        user['email'] = instance.org_email
        user.email = instance.org_email

        send_mail(
            template_name="suggestions/mails/suggestion_confirm.mail",
            subject=subject,
            to=user,
            suggestion=instance,
            tokenurl=tokenurl,
            language=instance.language
        )
