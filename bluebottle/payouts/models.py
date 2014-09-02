from bluebottle.bb_payouts.models import BaseProjectPayout, BaseOrganizationPayout
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.utils.model_dispatcher import get_project_model
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

PROJECT_MODEL = get_project_model()


class ProjectPayout(BaseProjectPayout):
    pass


class OrganizationPayout(BaseOrganizationPayout):
    pass


@receiver(post_save, weak=False, sender=PROJECT_MODEL)
def post_project_create_payout(sender, instance, created, **kwargs):

    project = instance
    if instance.status == ProjectPhase.objects.get(slug='realised'):
        payout, created = ProjectPayout.objects.get_or_create(project=project)
