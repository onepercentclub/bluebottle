from django import forms
from django.views.generic import FormView
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

from bluebottle.journals.models import DonationJournal, ProjectPayoutJournal, OrganizationPayoutJournal
from .models import BankTransaction


def modelformfactory(model, rel_field):
    """
    ModelFormFactory for the journal models
    """
    form_class = forms.models.modelform_factory(
        model,
        fields=('amount', 'user_reference', 'description', rel_field),
        widgets={
            rel_field: ForeignKeyRawIdWidget(model._meta.get_field(rel_field).rel, admin.site)
        }
    )
    form_class.title = model._meta.verbose_name
    return form_class


class UnknownTransactionView(FormView):
    """
    Show the three forms at once, each one submittable to its own url/handler
    """
    model = BankTransaction
    related_models = [
        (DonationJournal, 'donation'),
        (ProjectPayoutJournal, 'payout'),
        (OrganizationPayoutJournal, 'payout'),
    ]
    template_name = 'admin/accounting/banktransaction/unknown_transaction.html'

    def get_form_class(self):
        return [modelformfactory(model, rel_field) for (model, rel_field) in self.related_models]

    def get_form(self, form_classes):
        return [form_class(**self.get_form_kwargs()) for form_class in form_classes]

    def get_context_data(self, **kwargs):
        kwargs['opts'] = self.model._meta
        return super(UnknownTransactionView, self).get_context_data(**kwargs)
