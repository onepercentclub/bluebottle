from django import forms
from django.core.exceptions import ValidationError
from django.forms import CharField, ModelChoiceField, Textarea, BooleanField
from django.utils.translation import gettext_lazy as _

from bluebottle.initiatives.models import InitiativePlatformSettings
from .messages.activity_manager import GrantApplicationNeedsWorkMessage, GrantApplicationApprovedMessage
from .models import GrantDonor, GrantFund
from ..utils.fields import MoneyFormField
from ..utils.forms import TransitionConfirmationForm


class GrantApplicationApproveForm(TransitionConfirmationForm):
    """
    Form for creating a GrantDonor object for a GrantApplication.
    """
    fund = ModelChoiceField(
        queryset=GrantFund.objects.all(),
        label=_("Grant Fund"),
        help_text=_("Select the grant fund for this donation"),
        required=True
    )

    amount = MoneyFormField(
        label=_("Amount"),
        help_text=_("Enter the grant amount"),
        required=True,
    )

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Message'),
        required=False,
        help_text=_(
            'You can customise the message to the applicant telling them their request has been granted and what the next steps are.'),
    )

    message = GrantApplicationApprovedMessage

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.target:
            self.fields["amount"].initial = self.instance.target

        settings = InitiativePlatformSettings.load()
        if settings.vet_organizations and self.instance.organization:
            self.fields['vet_organizations'] = BooleanField(
                label=_("Due diligence"),
                help_text=_("All the required checks have been completed."),
                required=False
            )

    def clean(self):
        amount = self.cleaned_data['amount']
        fund = self.cleaned_data['fund']

        if str(amount.currency) != fund.currency:
            raise ValidationError({'amount': _('Currency should match fund currency')})

        if amount.amount > fund.eventual_balance().amount:
            raise ValidationError({'amount': _('Insufficient funds')})

        settings = InitiativePlatformSettings.load()
        if (
            settings.vet_organizations and
            self.instance.organization and
            not self.cleaned_data.get('vet_organizations')
        ):
            raise ValidationError({
                'vet_organizations': _('Please verify that all required checks have been completed')}
            )

    def save(self, user=None):
        """
        Create and save a GrantDonor object.
        """
        if not self.is_valid():
            raise ValueError("Form must be valid before saving")

        custom_message = self.cleaned_data.get('custom_message')
        if custom_message:
            self.transition.custom_message = custom_message

        fund = self.cleaned_data["fund"]
        amount = self.cleaned_data["amount"]

        grant_donor = GrantDonor.objects.create(
            activity=self.instance, fund=fund, amount=amount, user=user
        )
        return grant_donor


class GrantApplicationNeedsWorkForm(TransitionConfirmationForm):
    title = _('Grant application needs work')

    message = GrantApplicationNeedsWorkMessage

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_('You can provide a custom message to the applicant explaining why the request needs work.'),
    )

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class GrantApplicationRejectedForm(TransitionConfirmationForm):
    title = _('Grant application rejected')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the applicant explaining why their request was rejected.'),
    )

    @staticmethod
    def get_message_class():
        from bluebottle.grant_management.messages.activity_manager import GrantApplicationRejectedMessage
        return GrantApplicationRejectedMessage

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class GrantPayoutApproveForm(TransitionConfirmationForm):
    """
    Form for approving a grant payout with extra check
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, "activity"):
            # Set bank details
            try:
                bank_info = self.instance.activity.bank_account.account
                self.fields["bank_details"].initial = self._get_bank_details(bank_info)
            except Exception:
                self.fields["bank_details"].initial = "Error retrieving bank details"

            # Set account/KYC details
            try:
                account = self.instance.activity.bank_account.connect_account.account
                self.fields["account_details"].initial = self._get_account_details(
                    account
                )
            except Exception:
                self.fields["account_details"].initial = (
                    "Error retrieving account details"
                )

    bank_details = CharField(
        label=_("Bank details"),
        help_text=_("Bank account information"),
        widget=Textarea(
            attrs={"rows": 6, "readonly": True, "style": "font-family: monospace;"}
        ),
        required=False,
    )

    account_details = CharField(
        label=_("KYC details"),
        help_text=_("Know Your Customer information"),
        widget=Textarea(
            attrs={"rows": 6, "readonly": True, "style": "font-family: monospace;"}
        ),
        required=False,
    )

    def _get_bank_details(self, bank_info):
        """Helper method to get bank details as formatted text"""
        try:
            # Extract key information from bank_info and format as plain text
            details = []
            if hasattr(bank_info, "bank_name"):
                details.append(f"Bank: {bank_info.bank_name}")
            if hasattr(bank_info, "last4"):
                details.append(f"Last 4 digits: ****{bank_info.last4}")
            if hasattr(bank_info, "country"):
                details.append(f"Country: {bank_info.country}")
            if hasattr(bank_info, "currency"):
                details.append(f"Currency: {bank_info.currency}")

            return "\n".join(details) if details else "Bank details not available"
        except Exception as e:
            return f"Error retrieving details: {e}"

    def _get_account_details(self, account):
        """Helper method to get account details as formatted text"""
        individual = account.get("individual", None)
        business = account.get("business_profile", None)

        if individual:
            try:
                details = []
                if individual.get("first_name"):
                    details.append(f"First Name: {individual['first_name']}")
                if individual.get("last_name"):
                    details.append(f"Last Name: {individual['last_name']}")
                if individual.get("email"):
                    details.append(f"Email: {individual['email']}")
                if individual.get("phone"):
                    details.append(f"Phone: {individual['phone']}")
                if individual.get("dob", {}).get("day"):
                    dob = individual["dob"]
                    details.append(
                        f"Date of Birth: {dob.get('day')}/{dob.get('month')}/{dob.get('year')}"
                    )

                return (
                    "\n".join(details)
                    if details
                    else "Individual details not available"
                )
            except Exception as e:
                return f"Error rendering individual details: {e}"
        elif business:
            try:
                details = []
                if business.get("name"):
                    details.append(f"Business Name: {business['name']}")
                if business.get("url"):
                    details.append(f"Business URL: {business['url']}")
                if business.get("mcc"):
                    details.append(f"MCC: {business['mcc']}")

                return (
                    "\n".join(details) if details else "Business details not available"
                )
            except Exception as e:
                return f"Error rendering business details: {e}"
        else:
            return _("Account details not available")

    def save(self, user=None):
        return
