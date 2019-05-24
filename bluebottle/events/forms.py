from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Geolocation


class EventSubmitForm(forms.Form):
    title = forms.CharField(required=True, label=_('Title'))
    description = forms.CharField(required=True, label=_('Description'), widget=forms.Textarea)

    location = forms.ModelChoiceField(Geolocation.objects, required=True, label=_('Location'))
    location_hint = forms.CharField(label=_('Location hint'))

    start = forms.DateTimeField(required=True, label=_('Start'), widget=AdminSplitDateTime)
    end = forms.DateTimeField(required=True, label=_('End'), widget=AdminSplitDateTime)
    registration_deadline = forms.DateTimeField(label=_('Registration deadline'), widget=AdminSplitDateTime)

    capacity = forms.IntegerField(label=_('Attendee limit'))

    class Meta:
        fields = [
            'owner',
            'initiative',
            'title',
            'description',
            'location',
            'location_hint',
            'start',
            'end',
            'registration_deadline',
            'capacity'
        ]
