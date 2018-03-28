import geocoder

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver, Signal
from django.utils.translation import ugettext_lazy as _

from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.utils.email_backend import send_mail

# This signal indicates that the supplied project has been funded.
#
# :param first_time_funded: Whether or not the project has reached the funded state before. For instance, a project
#                           can become "unfunded" when a donation that was pending fails.
#
project_funded = Signal(providing_args=["first_time_funded"])


ROLE_NAMES = {
    'task_manager': _('Task manager'),
    'reviewer': _('Project reviewer'),
    'promoter': _('Project promoter'),
}


@receiver(pre_save, weak=False, sender='projects.Project')
def send_new_role_email(sender, instance, **kwargs):
    """ Send an email if a project role is assigned.
    """
    if not instance.pk:
        return

    from bluebottle.projects.models import Project

    original = Project.objects.get(pk=instance.pk)
    for role in ['task_manager', 'reviewer', 'promoter']:
        user = getattr(instance, role)
        if user and getattr(original, role) != user:
            # The original is not the same as the current: sent email
            with TenantLanguage(user.primary_language):
                role_name = ROLE_NAMES[role]
                subject = _(
                    _('You are assigned as %(role)s for project %(project)s') % {
                        'role': role_name, 'project': instance.title
                    }
                )

            if role == 'reviewer':
                link = reverse('admin:projects_project_change', args=(instance.pk, ))
            else:
                link = '/projects/{}'.format(instance.slug)

            send_mail(
                template_name='projects/mails/project_role.mail',
                subject=subject,
                to=user,
                receiver_name=user.short_name,
                role=role,
                role_name=role_name,
                title=instance.title,
                admin_email=properties.TENANT_MAIL_PROPERTIES.get('address'),
                link=link

            )


@receiver(pre_save, weak=False, sender='projects.ProjectLocation')
def save(sender, instance, **kwargs):
    try:
        current_instance = sender.objects.get(pk=instance.pk)
        if (
            current_instance.longitude and instance.longitude == current_instance.longitude and
            current_instance.latitude and instance.latitude == current_instance.latitude
        ):
            return
    except sender.DoesNotExist:
        pass  # Object is new, so field hasn't technically changed, but you may want to do something else here.

    if hasattr(settings, 'MAPS_API_KEY') and settings.MAPS_API_KEY:
        try:
            result = geocoder.google(
                [instance.latitude, instance.longitude],
                method='reverse',
                key=settings.MAPS_API_KEY,
                language=instance.project.language.code if instance.project.language else None
            )[0]

            if result.street_long != 'Unnamed Road':
                instance.street = result.street_long
            instance.neighborhood = result.neighborhood or result.sublocality
            instance.postal_code = result.postal
            instance.city = result.locality
            instance.country = result.country_long
        except IndexError:
            pass
