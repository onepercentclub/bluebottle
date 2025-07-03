from django.forms import ModelChoiceField
from django.utils.translation import gettext_lazy as _

from ..utils.fields import MoneyFormField
from ..utils.forms import TransitionConfirmationForm
from .models import GrantDonor, GrantFund


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
    )

    amount = MoneyFormField(
        label=_("Amount"),
        help_text=_("Enter the grant amount"),
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
