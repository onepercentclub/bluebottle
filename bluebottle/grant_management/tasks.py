import logging
from celery import shared_task
from django.utils import timezone

from .models import GrantProvider

logger = logging.getLogger(__name__)


@shared_task
def process_grant_provider_payments():
    """
    Task that runs every Monday at 9:00 AM to process grant provider payments
    based on their payment frequency and current week number.
    """
    current_date = timezone.now()
    current_week = current_date.isocalendar()[1]  # Get ISO week number

    logger.info(f"Starting grant provider payment processing for week {current_week}")

    # Get all grant providers
    grant_providers = GrantProvider.objects.all()

    processed_count = 0
    for provider in grant_providers:
        try:
            # Check if this provider should be processed this week
            frequency = int(provider.payment_frequency)

            # Process every week if frequency is 1, every 2 weeks if 2, every 4 weeks if 4
            if current_week % frequency == 0:
                logger.info(f"Processing payments for provider {provider.name} (frequency: {frequency})")
                provider.generate_payment()
                processed_count += 1
            else:
                logger.debug(
                    f"Skipping provider {provider.name} - "
                    f"not due this week (frequency: {frequency}, week: {current_week})"
                )

        except Exception as e:
            logger.error(f"Error processing payments for provider {provider.name}: {str(e)}")

    logger.info(f"Completed grant provider payment processing. Processed {processed_count} providers.")
    return processed_count
