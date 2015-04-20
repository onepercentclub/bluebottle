
from django.db import transaction as db_transaction
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, CreateView
from django.views.generic.detail import SingleObjectMixin

from bluebottle.journals.models import ProjectPayoutJournal, OrganizationPayoutJournal
from bluebottle.utils.model_dispatcher import get_order_model, get_donation_model
from bluebottle.utils.utils import StatusDefinition
from .models import BankTransaction
from .admin_forms import journalform_factory, donationform_factory


class UnknownTransactionView(SingleObjectMixin, FormView):

    """
    Show the three forms at once, each one submittable to its own url/handler
    """
    model = BankTransaction
    queryset = BankTransaction.objects.filter(status=BankTransaction.IntegrityStatus.UnknownTransaction)
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
        return {
            'amount': self.object.amount,
            'user_reference': self.request.user.email,
            'description': 'Entry for bank transaction %d that could not be matched automatically' % self.object.id,
        }

    def get_form_data(self, form_class):
        if not hasattr(self, '_form_data'):
            self._form_data = self.request.session.get('form_data')
            self._form_class = self.request.session.get('form_class')
            if self._form_data is not None:
                del self.request.session['form_data']
                del self.request.session['form_class']
        return self._form_data if self._form_class == form_class.__name__ else None

    def get_form_kwargs(self, form_class):
        kwargs = super(UnknownTransactionView, self).get_form_kwargs()
        kwargs['transaction'] = self.object
        if self.get_form_data(form_class) is not None:
            kwargs['data'] = self.get_form_data(form_class)
        return kwargs

    def get_donation_form(self, **kwargs):
        form_class = donationform_factory()
        if self.get_form_data(form_class) is not None:
            kwargs.setdefault('data', self.get_form_data(form_class))
        initial = self.get_initial()
        initial['anonymous'] = True
        form = form_class(initial=initial, transaction=self.object, **kwargs)
        return form

    def get_form_class(self):
        return [journalform_factory(model, rel_field) for (model, rel_field) in self.related_models]

    def get_form(self, form_classes):
        return (
            [self.get_donation_form()] +
            [form_class(**self.get_form_kwargs(form_class)) for form_class in form_classes]
        )

    def get_context_data(self, **kwargs):
        kwargs['opts'] = self.model._meta
        return super(UnknownTransactionView, self).get_context_data(**kwargs)


class BaseManualEntryView(CreateView):

    """
    Base view that holds the common logic for manual entries
    """
    success_url = reverse_lazy('admin:accounting_banktransaction_changelist')

    def get_transaction(self):
        return self.get_object(queryset=BankTransaction.objects.all())

    def get_form_kwargs(self):
        kwargs = super(BaseManualEntryView, self).get_form_kwargs()
        kwargs['transaction'] = self.get_transaction()
        return kwargs

    def form_invalid(self, form):
        """
        Store the form data in the session and show the errors on the originating page.
        """
        self.request.session['form_class'] = form.__class__.__name__
        self.request.session['form_data'] = form.data
        return redirect('admin:banktransaction-unknown', pk=form.transaction.pk)


class CreateDonationView(BaseManualEntryView):

    def get_form_class(self):
        return donationform_factory()

    def form_valid(self, form):
        transaction = form.transaction
        Order = get_order_model()
        with db_transaction.atomic():
            # create an order. we specify the user, because the donation itself
            # is marked as anonymous
            order = Order.objects.create(
                user=self.request.user,
                status=StatusDefinition.SUCCESS,  # completed
                order_type='manual_entry_unmatched_banktransaction',
                total=form.cleaned_data['amount'],
                completed=timezone.now()
            )
            form.instance.order = order
            response = super(CreateDonationView, self).form_valid(form)
            transaction.status = BankTransaction.IntegrityStatus.Valid
            transaction.save()
        messages.success(
            self.request,
            _('Created a new donation and manually resolved transaction "%s"') % transaction
        )
        return response


class JournalCreateMixin(object):

    """
    Mixin that provides a ModelForm factory and form_valid handler.
    """

    def get_form_class(self):
        return journalform_factory(self.model, 'payout')

    def form_valid(self, form):
        transaction = form.transaction
        with db_transaction.atomic():
            response = super(JournalCreateMixin, self).form_valid(form)
            transaction.status = BankTransaction.IntegrityStatus.Valid
            transaction.save()
            messages.success(
                self.request,
                _('A journal entry was created to resolve transaction "%s"') % transaction
            )
        return response


class CreateProjectPayoutJournalView(JournalCreateMixin, BaseManualEntryView):
    model = ProjectPayoutJournal
    fields = ('amount', 'user_reference', 'description', 'payout')


class CreateOrganizationPayoutJournalView(JournalCreateMixin, BaseManualEntryView):
    model = OrganizationPayoutJournal
    fields = ('amount', 'user_reference', 'description', 'payout')


class CreateManualDonationView(BaseManualEntryView):
    model = get_donation_model()
    form_class = donationform_factory(fields=('amount', 'project', 'fundraiser'))
    template_name = 'admin/accounting/banktransaction/manual_donation.html'

    def dispatch(self, *args, **kwargs):
        self.transaction = self.get_transaction()
        return super(CreateManualDonationView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CreateManualDonationView, self).get_initial()
        initial['amount'] = self.transaction.amount
        return initial

    def form_valid(self, form):
        import bpdb; bpdb.set_trace()

    def get_context_data(self, **kwargs):
        kwargs['transaction'] = self.transaction
        kwargs['opts'] = self.model._meta
        return super(CreateManualDonationView, self).get_context_data(**kwargs)
