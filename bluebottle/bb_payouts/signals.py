from decimal import Decimal
from datetime import timedelta
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.utils.model_dispatcher import get_project_payout_model
from bluebottle.utils.utils import StatusDefinition

from django.utils import timezone


def create_payout_finished_project(sender, instance, created, **kwargs):
    """
    Create or update Payout for finished projects.
    Project finish when deadline is hit or when it's changed manually in admin.
    """

    project = instance
    now = timezone.now()

    if project.is_realised and project.amount_asked:

        if now.day <= 15:
            next_date = timezone.datetime(now.year, now.month, 15)
        else:
            next_date = timezone.datetime(now.year, now.month, 1) + timedelta(days=20)

        PROJECT_PAYOUT_MODEL = get_project_payout_model()

        try:
            # Update existing Payout
            payout = PROJECT_PAYOUT_MODEL.objects.get(project=project)

            if payout.status == StatusDefinition.NEW:
                # Update planned payout date for new Payouts
                payout.calculate_amounts()
                payout.planned = next_date
                payout.save()

        except PROJECT_PAYOUT_MODEL.DoesNotExist:

            # Create new Payout
            payout = PROJECT_PAYOUT_MODEL(
                planned=next_date,
                project=project
            )

            # Calculate amounts
            payout.calculate_amounts()

            # Set payment details
            organization = project.organization
            payout.receiver_account_bic = organization.account_bic
            payout.receiver_account_iban = organization.account_iban
            payout.receiver_account_number = organization.account_number
            payout.receiver_account_name = organization.account_holder_name
            payout.receiver_account_city = organization.account_holder_city
            payout.receiver_account_country = organization.account_bank_country

            # Generate invoice reference, saves twice
            payout.update_invoice_reference(auto_save=True)
