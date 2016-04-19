from django.template.loader import get_template

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url

from bluebottle.utils.email_backend import send_mail
from django.utils.translation import ugettext as _


def mail_project_funded_internal(project):
    # XXX This is most likely obsolete. Candidate for removal?
    context = ClientContext(
        {'project': project,
         'link': '/go/projects/{0}'.format(project.slug),
         'site': tenant_url()})

    subject = "A project has been funded"
    text_content = get_template('project_funded_internal.mail.txt').render(
        context)
    html_content = get_template('project_funded_internal.mail.html').render(
        context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content,
                                 to=['project@onepercentclub.com'])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def mail_project_complete(project):
    with TenantLanguage(project.owner.primary_language):
        subject = _(u"The project '{0}' has been realised").format(project.title)

    send_mail(
        template_name="projects/mails/project_complete.mail",
        subject=subject,
        to=project.owner,
        title=project.title,
        receiver_name=project.owner.short_name,
        site=tenant_url(),
        link='/go/projects/{0}'.format(project.slug)
    )


def mail_project_incomplete(project):
    with TenantLanguage(project.owner.primary_language):
        subject = _(u"The project '{0}' has expired").format(project.title)

    send_mail(
        template_name="projects/mails/project_incomplete.mail",
        subject=subject,
        to=project.owner,
        title=project.title,
        receiver_name=project.owner.short_name,
        site=tenant_url(),
        link='/go/projects/{0}'.format(project.slug)
    )
