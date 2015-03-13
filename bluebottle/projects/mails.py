from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url
from django.template.loader import get_template


def mail_project_funded_internal(project):
    context = ClientContext(
                       {'project': project,
                       'link': '/go/projects/{0}'.format(project.slug),
                       'site': tenant_url()})
    subject = "A project has been funded"
    text_content = get_template('project_funded_internal.mail.txt').render(context)
    html_content = get_template('project_funded_internal.mail.html').render(context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=['project@onepercentclub.com'])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
