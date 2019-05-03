from django import forms
from django.utils.translation import ugettext_lazy as _

from bluebottle.initiatives.models import Initiative


class InitiativeSubmitForm(forms.Form):
    title = forms.CharField(required=True, label=_('Title'))
    pitch = forms.CharField(required=True, label=_('Pitch'))
    story = forms.CharField(required=True, label=_('Story'))

    class Meta:
        model = Initiative
        fields = ['title', 'pitch', 'story', 'theme', 'image', 'owner', 'place']
