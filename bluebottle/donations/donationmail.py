from django.utils import translation
from django.utils.translation import ugettext as _
from bluebottle.utils.email_backend import send_mail

from bluebottle.clients.utils import tenant_url
from bluebottle.clients import properties


def successful_donation_fundraiser_mail(instance):

    # should be only when the status is success
    try:
        receiver = instance.fundraiser.owner
    except:
        # donation it's not coming from a fundraiser
        return

    fundraiser_link = '/go/fundraisers/{0}'.format(instance.fundraiser.id)

    if instance.fundraiser.owner.email:

        if instance.anonymous:
            donor_name = _('an anonymous person')
        elif instance.order.user:
            if instance.order.user.first_name:
                donor_name = instance.order.user.first_name
            else:
                donor_name = instance.order.user.email
        else:
            donor_name = _('a guest')

    cur_language = translation.get_language()
    if receiver and receiver.primary_language:
        translation.activate(receiver.primary_language)
    else:
        translation.activate(properties.LANGUAGE_CODE)

    subject = _('You received a new donation')

    translation.activate(cur_language)

    send_mail(
        template_name='donations/mails/new_oneoff_donation_fundraiser.mail',
        subject=subject,
        site=tenant_url(),
        to=receiver,
        amount=instance.amount,
        donor_name=donor_name,
        link=fundraiser_link,
        first_name=receiver.first_name
    )


def new_oneoff_donation(instance):
    """
    Send project owner a mail if a new "one off" donation is done.
    We consider a donation done if the status is pending.
    """
    donation = instance

    # Only process "one-off" type donations
    if donation.order.order_type != "one-off":
        return

    project_url = '/go/projects/{0}'.format(donation.project.slug)

    if donation.project.owner.email:

        if donation.anonymous:
            donor_name = _('an anonymous person')
        elif donation.order.user:
            donor_name = donation.order.user.first_name
        else:
            donor_name = _('a guest')

        receiver = donation.project.owner

        cur_language = translation.get_language()

        if receiver and receiver.primary_language:
            translation.activate(receiver.primary_language)
        else:
            translation.activate(properties.LANGUAGE_CODE)

        subject = _('You received a new donation')

        translation.activate(cur_language)

        # Send email to the project owner.
        send_mail(
            template_name='donations/mails/new_oneoff_donation.mail',
            subject=subject,
            to=receiver,
            amount=donation.amount,
            donor_name=donor_name,
            link=project_url,
            first_name=donation.project.owner.first_name
        )

    # TODO: This is the logic for sending mail to a supporter once he/she has
    # donated.
    # if donation.order.user.email:
    #     # Send email to the project supporter
    #     send_mail(
    #         template_name="donations/new_oneoff_donation.mail",
    #         subject=_("You supported {0}".format(donation.project.title)),
    #         to=donation.order.user,
    #         link=project_url
    #     )
