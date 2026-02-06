from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Actor, Follow, PublishModeChoices
from bluebottle.activity_pub.utils import get_platform_actor


class SharePublishForm(forms.Form):
    title = _('Share activity')
    old_recipients = forms.ModelMultipleChoiceField(
        label=_('Already shared with'),
        required=False,
        queryset=Actor.objects.none(),
        widget=forms.Textarea(attrs={'readonly': True, 'rows': 3}),
        help_text=_('These partners are already recipients and cannot be changed here.'),
    )
    recipients = forms.ModelMultipleChoiceField(
        label=_('Partners'),
        required=False,
        queryset=Actor.objects.none(),
        help_text=_('Partners that will receive this activity.'),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)

        old_recipient_ids = []
        old_recipients = []
        try:
            publish = obj.event.create_set.first()
            if publish:
                # Recipients are Recipient objects, extract the actors
                old_recipients = [r.actor for r in publish.recipients.all()]
                old_recipient_ids = [r.actor.id for r in publish.recipients.all()]
        except (ObjectDoesNotExist, AttributeError):
            pass

        self.fields['old_recipients'].initial = old_recipients

        accepted_follow_ids = Follow.objects.exclude(
            actor__id__in=old_recipient_ids
        ).filter(
            object=get_platform_actor(),
            accept__isnull=False,
        ).values_list('actor_id', flat=True)

        accepted_follow_ids = list(accepted_follow_ids)

        self.fields['recipients'].queryset = Actor.objects.filter(pk__in=accepted_follow_ids)
        self.initial['recipients'] = self.fields['recipients'].queryset
        self.initial['recipients'].initial = accepted_follow_ids

        if not accepted_follow_ids:
            self.fields['recipients'].help_text = _(
                'No additional partners available to share with.'
            )


class AcceptFollowPublishModeForm(forms.Form):
    title = _('Accept follow request')

    publish_mode = forms.ChoiceField(
        label=_('Publish mode'),
        choices=PublishModeChoices.choices,
        required=True,
        help_text=_('Select how activities from this partner should be shared.'),
        widget=forms.RadioSelect()
    )

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        if obj:
            self.fields['publish_mode'].initial = obj.publish_mode


class PublishActivitiesForm(forms.Form):
    title = _('Publish all activities')
