from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Follow, Publish
from bluebottle.activity_pub.utils import get_platform_actor


class PlatformMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        if 'queryset' not in kwargs:
            kwargs['queryset'] = Follow.objects.filter(object=get_platform_actor())

        super().__init__(*args, **kwargs)
    
    def label_from_instance(self, obj):
        """Return the Actor's string representation as the label."""
        return str(obj.actor)


class ImpactReminderConfirmationForm(forms.Form):
    title = _('Send impact reminder message')


class PublishActivityForm(forms.Form):
    title = _('Publish activity to other platforms')

    platforms = PlatformMultipleChoiceField(
        required=False,
        queryset=Follow.objects.all(),
        label=_('Platforms'),
        widget=forms.CheckboxSelectMultiple
    )
