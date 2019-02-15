from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html


class UploadWidget(forms.FileInput):
    def render(self, name, value, attrs=None):
        html = super(UploadWidget, self).render(name, value, attrs)
        if value:
            text = _('Change:')
        else:
            text = _('Add:')

        html = format_html(
            '<p class="url">{0} {1}</p>',
            text, html
        )
        return html


class RefundConfirmationForm(forms.Form):
    title = _('Refund project?!')


class PayoutApprovalConfirmationForm(forms.Form):
    title = _('Approve Payout?!')
