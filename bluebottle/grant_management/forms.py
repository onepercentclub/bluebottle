from django.forms import CharField, ModelChoiceField, Textarea
from django.utils.translation import gettext_lazy as _

from .models import GrantDonor, GrantFund
from ..utils.fields import MoneyFormField
from ..utils.forms import TransitionConfirmationForm


class GrantApplicationApproveForm(TransitionConfirmationForm):
    """
    Form for creating a GrantDonor object for a GrantApplication.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.target:
            self.fields["amount"].initial = self.instance.target

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

    def save(self, user=None):
        """
        Create and save a GrantDonor object.
        """
        if not self.is_valid():
            raise ValueError("Form must be valid before saving")

        fund = self.cleaned_data["fund"]
        amount = self.cleaned_data["amount"]

        grant_donor = GrantDonor.objects.create(
            activity=self.instance, fund=fund, amount=amount, user=user
        )

        return grant_donor


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
