from django.utils.safestring import mark_safe

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.utils import tenant_url

from bluebottle.surveys.models import Survey

from bluebottle.utils.email_backend import send_mail
from django.utils.translation import ugettext as _


def mail_project_complete(project):
    with TenantLanguage(project.owner.primary_language):
        subject = _(u"The project '{0}' has been realised").format(project.title)

    survey_link = Survey.url(project, user_type='initiator')

    send_mail(
        template_name="projects/mails/project_complete.mail",
        subject=subject,
        to=project.owner,
        title=project.title,
        receiver_name=project.owner.short_name,
        survey_link=mark_safe(survey_link) if survey_link else None,
        site=tenant_url(),
        link='/go/projects/{0}'.format(project.slug)
    )

    if project.organization:
        with TenantLanguage(project.owner.primary_language):
            subject = _(u"The project '{0}' has been realised").format(project.title)

        survey_link = Survey.url(project, user_type='organization')

        send_mail(
            template_name="projects/mails/organization_project_complete.mail",
            subject=subject,
            to=project.organization,
            title=project.title,
            receiver_name=project.organization.name,
            survey_link=mark_safe(survey_link) if survey_link else None,
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
