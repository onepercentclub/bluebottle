from __future__ import absolute_import
import math
import logging
from celery import shared_task
from collections import namedtuple
from moneyed import Money

from django.db import connection
from django.utils.timezone import now
from django.utils import timezone

from django_fsm import TransitionNotAllowed

from rest_framework.exceptions import MethodNotAllowed

from bluebottle.clients.utils import LocalTenant
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.projects.models import Project
from bluebottle.recurring_donations.models import MonthlyProject
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments.services import PaymentService

from .models import MonthlyDonor, MonthlyDonation, MonthlyOrder, MonthlyBatch
from .mails import mail_monthly_donation_processed_notification

PAYMENT_METHOD = 'docdataDirectdebit'

logger = logging.getLogger(__name__)


@shared_task
def process_monthly_batch(tenant, monthly_batch, send_email):
    """
    Process monthly donations
    :param tenant: The tenant.
    :param monthly_batch: The monthly donation batch to process
    :param send_email: Are emails to be send or do we run this quietly.
    :return:
    """
    connection.set_tenant(tenant)
    with LocalTenant(tenant, clear_tenant=True):

        if not monthly_batch:
            logger.info("No batch found using latest...")
            monthly_batch = MonthlyBatch.objects.order_by('-date', '-created').all()[0]

        if monthly_batch.status != 'new':
            raise MethodNotAllowed("Can only process monthlys batch with status 'New'")
        else:
            results = []
            monthly_batch.status = 'processing'
            monthly_batch.save()
            for monthly_order in monthly_batch.orders.all():
                result = _process_monthly_order(monthly_order, send_email)
                results.append(result)
            monthly_batch.status = 'done'
            monthly_batch.save()

        # post process the results
        for result in results:
            if 'order_payment_id' in result and not result['processed']:
                order_payment = OrderPayment.objects.get(id=result['order_payment_id'])

                # set the order payment to failed
                try:
                    order_payment.failed()
                except TransitionNotAllowed:
                    if order_payment.status == StatusDefinition.CREATED:
                        order_payment.started()
                        order_payment.failed()

                order_payment.save()


def prepare_monthly_batch():
    """
    Prepare MonthlyOrders.
    """

    ten_days_ago = timezone.now() + timezone.timedelta(days=-10)
    recent_batches = MonthlyBatch.objects.filter(date__gt=ten_days_ago)
    if recent_batches.count() > 0:
        recent_batch = recent_batches.all()[0]
        message = "Found a recent batch {0} : {1}. Refusing to create another one quite now.".format(
            recent_batch.id, recent_batch)
        logger.error(message)
        return

    batch = MonthlyBatch.objects.create(date=now())
    batch.save()

    donor_queryset = MonthlyDonor.objects.filter(active=True).order_by(
        'user__email')

    recurring_donation_errors = []
    RecurringDonationError = namedtuple('RecurringDonationError',
                                        'recurring_payment error_message')
    skipped_recurring_payments = []

    donation_count = 0

    popular_projects_all = Project.objects.\
        exclude(skip_monthly=True, amount_needed=0).\
        filter(status=ProjectPhase.objects.get(slug="campaign")).\
        order_by('-popularity')

    top_three_projects = list(popular_projects_all[:3])
    top_projects = list(popular_projects_all[3:])

    logger.info("Config: Using these projects as 'Top Three':")
    for project in top_three_projects:
        logger.info("  {0}".format(project.title.encode("utf8")))

    # The main loop that processes each monthly donation.
    for donor in donor_queryset:

        # Remove DonorProjects for Projects that no longer need money.
        # This is amount_needed from db minus the amount already appointed in previous MonthlyDonations
        for donor_project in donor.projects.all():
            if donor_project.project.status != ProjectPhase.objects.get(
                    slug="campaign"):
                donor_project.delete()
            elif donor_project.project.amount_needed.amount <= 0:
                donor_project.delete()
            else:
                monthly_project, created = MonthlyProject.objects.get_or_create(
                    batch=batch, project=donor_project.project)
                if donor_project.project.amount_needed.amount - monthly_project.amount.amount <= 0:
                    donor_project.delete()

        # Remove Projects from top 3
        for project in top_three_projects:
            monthly_project, created = MonthlyProject.objects.get_or_create(
                batch=batch, project=project)
            if project.amount_needed.amount - monthly_project.amount.amount <= 0:
                # Remove project if it's doesn't need more many and add another from top_projects
                top_three_projects.remove(project)
                new_project = top_projects.pop(0)
                top_three_projects.append(new_project)

        # Check if the donor object is valid
        if not donor.is_valid:
            error_message = "MonthlyDonor [{0}] invalid! IBAN/BIC missing or amount wrong.".format(
                donor.id)
            logger.error(error_message)
            recurring_donation_errors.append(
                RecurringDonationError(donor, error_message))
            continue

        # Create MonthlyOrder and MonthlyDonation objects
        if donor.projects.count():
            # Prepare a MonthlyOrder with preferred projects
            preferred_projects = []
            for project in donor.projects.all():
                preferred_projects.append(project.project)
            recurring_order = create_recurring_order(donor.user,
                                                     preferred_projects, batch,
                                                     donor)
        else:
            # Prepare MonthlyOrder with Donations for the top three projects.
            recurring_order = create_recurring_order(donor.user,
                                                     top_three_projects, batch,
                                                     donor)
        # Update amounts for projects
        for donation in recurring_order.donations.all():
            monthly_project, created = MonthlyProject.objects.get_or_create(
                batch=batch, project=donation.project)
            monthly_project.amount += donation.amount
            monthly_project.save()

        # Safety check to ensure the modifications to the donations in the recurring result
        # in an Order total that matches the RecurringDirectDebitPayment.
        if donor.amount != recurring_order.amount:
            error_message = ("Monthly donation amount: {0} does not equal recurring "
                             "Order amount: {1} for '{2}'. Not processing this recurring "
                             "donation.").format(donor.amount, recurring_order.amount, donor)
            logger.error(error_message)
            recurring_donation_errors.append(
                RecurringDonationError(donor, error_message))
            continue

    logger.info("")
    logger.info("Recurring Donation Preparing Summary")
    logger.info("=====================================")
    logger.info("")
    logger.info("Total number of recurring donations: {0}".format(
        donor_queryset.count()))
    logger.info("Number of recurring Orders successfully processed: {0}".format(
        donation_count))
    logger.info("Number of errors: {0}".format(len(recurring_donation_errors)))
    logger.info("Number of skipped payments: {0}".format(
        len(skipped_recurring_payments)))

    if len(recurring_donation_errors) > 0:
        logger.info("")
        logger.info("")
        logger.info("Detailed Error List")
        logger.info("===================")
        logger.info("")
        for error in recurring_donation_errors:
            logger.info("RecurringDirectDebitPayment: {0} {1}".format(
                error.recurring_payment.id, error.recurring_payment))
            logger.info("Error: {0}".format(error.error_message))
            logger.info("--")

    if len(skipped_recurring_payments) > 0:
        logger.info("")
        logger.info("")
        logger.info("Skipped Recurring Payments")
        logger.info("==========================")
        logger.info("")
        for skipped_payment in skipped_recurring_payments:
            logger.info("RecurringDirectDebitPayment: {0} {1}".format(
                skipped_payment.recurring_payment.id,
                skipped_payment.recurring_payment))
            for closed_order in skipped_payment.orders:
                logger.info("Order Number: {0}".format(closed_order.id))
                logger.info("--")

    return batch


def create_recurring_order(user, projects, batch, donor):
    """
    Creates a recurring Order with donations to the supplied projects.
    """
    project_amount = Money((math.floor(donor.amount.amount * 100 / len(projects)) / 100), 'EUR')
    order = MonthlyOrder.objects.create(user=user, batch=batch,
                                        amount=donor.amount, name=donor.name,
                                        city=donor.city, iban=donor.iban,
                                        bic=donor.bic,
                                        country=donor.country.alpha2_code)
    order.save()

    rest_amount = donor.amount - project_amount * len(projects)

    project_count = len(projects)
    for index, project in enumerate(projects):
        amount = project_amount if index < project_count - 1 else project_amount + rest_amount
        don = MonthlyDonation.objects.create(user=user, project=project,
                                             amount=amount, order=order)
        don.save()

    return order


def _process_monthly_order(monthly_order, send_email=False):
    if monthly_order.processed:
        logger.info(
            "Order for {0} already processed".format(monthly_order.user))
        return {
            'order_payment_id': None,
            'processed': True
        }

    order_success = [StatusDefinition.PENDING, StatusDefinition.SUCCESS]
    ten_days_ago = timezone.now() + timezone.timedelta(days=-10)
    recent_orders = Order.objects.filter(user=monthly_order.user,
                                         order_type='recurring',
                                         status__in=order_success,
                                         updated__gt=ten_days_ago)

    if recent_orders.count() > 0:
        message = "Skipping '{0}' recently processed a recurring order for {1}:".format(
            monthly_order, monthly_order.user)
        logger.warn(message)
        for closed_order in recent_orders.all():
            logger.warn("Recent Order Number: {0}".format(closed_order.id))

        # Set an error on this monthly order
        monthly_order.error = message
        monthly_order.save()
        return {
            'order_payment_id': None,
            'processed': False
        }

    order = Order.objects.create(status=StatusDefinition.LOCKED,
                                 user=monthly_order.user,
                                 order_type='recurring')
    order.save()

    logger.info(
        "Creating Order for {0} with {1} donations".format(monthly_order.user,
                                                           monthly_order.donations.count()))
    for monthly_donation in monthly_order.donations.all():
        donation = Donation.objects.create(amount=monthly_donation.amount,
                                           project=monthly_donation.project,
                                           order=order)
        donation.save()

    integration_data = {'account_name': monthly_order.name,
                        'account_city': monthly_order.city,
                        'iban': monthly_order.iban,
                        'bic': monthly_order.bic,
                        'agree': True}

    order_payment = OrderPayment(order=order, user=monthly_order.user,
                                 payment_method=PAYMENT_METHOD,
                                 integration_data=integration_data)

    order_payment.save()

    try:
        service = PaymentService(order_payment)
        service.start_payment()
    except PaymentException as e:
        error_message = "Problem starting payment. {0}".format(e)
        monthly_order.error = "{0}".format(e.message)
        monthly_order.save()
        logger.error(error_message)
        return {
            'order_payment_id': order_payment.id,
            'processed': False
        }

    logger.debug("Payment for '{0}' started.".format(monthly_order))

    monthly_order.processed = True
    monthly_order.error = ''
    monthly_order.save()

    # Try to update status
    service.check_payment_status()

    # Send an email to the user.
    if send_email:
        mail_monthly_donation_processed_notification(monthly_order)

    return {
        'order_payment_id': order_payment.id,
        'processed': True
    }


def process_single_monthly_order(email, batch=None, send_email=False):
    if not batch:
        logger.info("No batch found using latest...")
        batch = MonthlyBatch.objects.order_by('-date', '-created').all()[0]

    monthly_orders = batch.orders.filter(user__email=email)
    if monthly_orders.count() > 1:
        logger.error("Found multiple MonthlyOrders for {0}.".format(email))
    elif monthly_orders.count() == 1:
        monthly_order = monthly_orders.get()
        _process_monthly_order(monthly_order, send_email)
    else:
        logger.error(
            "No MonthlyOrder found for {0} in Batch {1}.".format(email, batch))
