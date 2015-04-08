from django import forms
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

from bluebottle.journals.models import ProjectPayoutJournal, OrganizationPayoutJournal
from bluebottle.utils.model_dispatcher import get_donation_model
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


class UnknownTransactionView(SingleObjectMixin, FormView):

    """
    Show the three forms at once, each one submittable to its own url/handler
    """
    model = BankTransaction
    related_models = [
        (ProjectPayoutJournal, 'payout'),
        (OrganizationPayoutJournal, 'payout'),
    ]
    template_name = 'admin/accounting/banktransaction/unknown_transaction.html'
    context_object_name = 'transaction'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UnknownTransactionView, self).get(request, *args, **kwargs)

    def get_initial(self):
        return {'amount': self.object.amount}

    def get_donation_form(self):
        Donation = get_donation_model()
        widgets = {
            'project': ForeignKeyRawIdWidget(Donation._meta.get_field('project').rel, admin.site),
            'fundraiser': ForeignKeyRawIdWidget(Donation._meta.get_field('fundraiser').rel, admin.site),
            'order': ForeignKeyRawIdWidget(Donation._meta.get_field('order').rel, admin.site),
        }
        ModelForm = forms.models.modelform_factory(
            Donation,
            fields=('amount', 'project', 'fundraiser', 'order', 'anonymous'),
            widgets=widgets
        )
        ModelForm.title = Donation._meta.verbose_name
        return ModelForm(initial=self.get_initial())

    def get_form_class(self):
        return [modelformfactory(model, rel_field) for (model, rel_field) in self.related_models]

    def get_form(self, form_classes):
        return [self.get_donation_form()] + [form_class(**self.get_form_kwargs()) for form_class in form_classes]

    def get_context_data(self, **kwargs):
        kwargs['opts'] = self.model._meta
        return super(UnknownTransactionView, self).get_context_data(**kwargs)
