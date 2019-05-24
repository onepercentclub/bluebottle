from django import forms
from django.utils.translation import ugettext_lazy as _
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.files.models import Image
from bluebottle.geo.models import Geolocation


class InitiativeSubmitForm(forms.Form):
    title = forms.CharField(required=True, label=_('Title'))
    pitch = forms.CharField(required=True, label=_('Pitch'))
    story = forms.CharField(required=True, label=_('Story'))

    theme = forms.ModelChoiceField(ProjectTheme.objects, label=_('Theme'))
    image = forms.ModelChoiceField(Image.objects, label=_('Image'))
    place = forms.ModelChoiceField(Geolocation.objects, label=_('Place'))

    class Meta:
        fields = ['title', 'pitch', 'story', 'theme', 'image', 'owner', 'place']
