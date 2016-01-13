import logging

from django.core.exceptions import ValidationError

from bluebottle.utils.model_dispatcher import get_project_payout_model
from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger()


def create_payout_finished_project(sender, instance, created, **kwargs):
    """
    Create or update Payout for finished projects.
    Project finish when deadline is hit or when it's changed manually in admin.
    """
    from localflavor.generic.validators import IBANValidator

    PROJECT_PAYOUT_MODEL = get_project_payout_model()

    project = instance

    if project.status.slug in ['done-complete', 'done-incomplete'] \
            and project.amount_asked:

        PROJECT_PAYOUT_MODEL = get_project_payout_model()
        next_date = PROJECT_PAYOUT_MODEL.get_next_planned_date()

        try:
            # Update existing Payout
            payout = PROJECT_PAYOUT_MODEL.objects.get(project=project, protected=False)

            if payout.status == StatusDefinition.NEW:
                # Update planned payout date for new Payouts
                payout.calculate_amounts()
                payout.planned = next_date
                payout.save()

        except PROJECT_PAYOUT_MODEL.DoesNotExist:

            if project.campaign_started:
                # Create new Payout
                payout = PROJECT_PAYOUT_MODEL(
                    planned=next_date,
                    project=project
                )

                # Calculate amounts
                payout.calculate_amounts()

                if project.is_closed:
                    payout.status = StatusDefinition.SETTLED

                # Set payment details
                try:
                    IBANValidator()(project.account_number)
                    payout.receiver_account_iban = project.account_number
                except ValidationError as e:
                    logger.info(
                        "IBAN error payout {0}, project: {1}: {2}".format(
                            payout.id, project.id, e.message))

                payout.receiver_account_bic = project.account_bic
                payout.receiver_account_number = project.account_number
                payout.receiver_account_name = project.account_holder_name
                payout.receiver_account_city = project.account_holder_city
                payout.receiver_account_country = project.account_bank_country

                payout.save()
