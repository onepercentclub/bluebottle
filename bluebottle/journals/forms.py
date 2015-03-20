from django.forms import ModelForm
from .models import DonationJournal, ProjectPayoutJournal, OrganizationPayoutJournal


class DonationJournalForm(ModelForm):
    class Meta:
        model = DonationJournal
        exclude = ('user_reference', )


class ProjectPayoutJournalForm(ModelForm):
    class Meta:
        model = ProjectPayoutJournal
        exclude = ('user_reference', )


class OrganizationPayoutJournalForm(ModelForm):
    class Meta:
        model = OrganizationPayoutJournal
        exclude = ('user_reference', )
