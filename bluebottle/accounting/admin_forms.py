from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.model_dispatcher import get_donation_model
from bluebottle.journals.models import ProjectPayoutJournal
from bluebottle.bb_payouts.models import PayoutBase


class BaseManualEntryModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.transaction = kwargs.pop('transaction')
        super(BaseManualEntryModelForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount != self.transaction.amount:
            raise forms.ValidationError(_('The amount must be exactly equal to the transaction amount'))
        return amount


def journalform_factory(model, rel_field):
    """
    ModelFormFactory for the journal models
    """
    form_class = forms.models.modelform_factory(
        model,
        form=BaseManualEntryModelForm,
        fields=('amount', 'user_reference', 'description', rel_field),
        widgets={
            rel_field: ForeignKeyRawIdWidget(
                model._meta.get_field(rel_field).rel,
                admin.site,
                # attrs={'id': 'id_%s_payout' % model._meta.model_name}  # doesn't work because lookup_id is hardcoded
            ),
            'user_reference': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
    )
    form_class.title = model._meta.verbose_name
    form_class.url_name = 'admin:banktransaction-add-%s' % model._meta.model_name
    return form_class


def donationform_factory(fields=None):
    Donation = get_donation_model()
    widgets = {
        'project': ForeignKeyRawIdWidget(Donation._meta.get_field('project').rel, admin.site),
        'fundraiser': ForeignKeyRawIdWidget(Donation._meta.get_field('fundraiser').rel, admin.site),
        'order': ForeignKeyRawIdWidget(Donation._meta.get_field('order').rel, admin.site),
        'anonymous': forms.HiddenInput(),
    }
    ModelForm = forms.models.modelform_factory(
        Donation,
        form=BaseManualEntryModelForm,
        fields=fields or ('amount', 'project', 'fundraiser', 'order', 'anonymous'),
        widgets=widgets
    )
    ModelForm.title = Donation._meta.verbose_name
    ModelForm.url_name = 'admin:banktransaction-add-donation'
    return ModelForm


class RetryPayoutForm(forms.ModelForm):
    class Meta:
        model = ProjectPayoutJournal
        fields = ('payout', 'amount', 'description')
        widgets = {
            'payout': ForeignKeyRawIdWidget(ProjectPayoutJournal._meta.get_field('payout').rel, admin.site),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        transaction = kwargs.pop('transaction')
        kwargs['initial']['description'] = _('Retry bounced payout ({transaction}, <pk {pk}>)').format(transaction=transaction, pk=transaction.pk)
        super(RetryPayoutForm, self).__init__(*args, **kwargs)
        self.fields['payout'].queryset = self.fields['payout'].queryset.filter(status=PayoutBase.Statuses.SETTLED)
        self.fields['amount'].label = _('Bank costs')
        self.fields['amount'].help_text = _('Bank costs to compensate. This will be deducted from the payable amount')

RetryPayoutForm.title = _('Select payout to retry')
