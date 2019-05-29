from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Geolocation


class EventSubmitForm(forms.Form):
    title = forms.CharField(required=True, label=_('Title'))
    description = forms.CharField(required=True, label=_('Description'), widget=forms.Textarea)

    location = forms.ModelChoiceField(Geolocation.objects, required=True, label=_('Location'))

    start_time = forms.DateTimeField(required=True, label=_('Start'), widget=AdminSplitDateTime)
    end_time = forms.DateTimeField(required=True, label=_('End'), widget=AdminSplitDateTime)
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
            'start_time',
            'end_time',
            'registration_deadline',
            'capacity'
        ]
