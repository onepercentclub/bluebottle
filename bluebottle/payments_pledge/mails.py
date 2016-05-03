from django.template.loader import get_template

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url

from bluebottle.utils.email_backend import send_mail
from django.utils.translation import ugettext as _


def mail_pledge_project_owner(donation):
    project = donation.project

    with TenantLanguage(donation.user.primary_language):
        subject = _(u"The project '{0}' has received a pledge").format(project.title)

    send_mail(
        template_name="payments_pledge/mails/pledge_project_owner.mail",
        subject=subject,
        to=project.owner,
        title=project.title,
        receiver_name=project.owner.short_name,
        site=tenant_url(),
        link='/go/projects/{0}'.format(project.slug)
    )

def mail_pledge_donator(donation):
    project = donation.project

    with TenantLanguage(donation.user.primary_language):
        subject = _(u"You have pledged to the project '{0}'").format(project.title)

    send_mail(
        template_name="payments_pledge/mails/pledge_donator.mail",
        subject=subject,
        to=donation.user,
        title=project.title,
        receiver_name=donation.user.short_name,
        site=tenant_url(),
        link='/go/projects/{0}'.format(project.slug)
    )
