from django.conf.urls import url
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.utils.forms import TransitionConfirmationForm


def log_action(obj, user, change_message='Changed', action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=unicode(obj),
        action_flag=action_flag,
        change_message=change_message
    )


class StateMachineAdminMixin(object):
    form = StateMachineModelForm

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Determines the HttpResponse for the change_view stage.
        """
        if object_id and request.method == 'POST' and not request.POST.get('confirm', False):
            obj = self.model.objects.get(pk=object_id)
            ModelForm = self.get_form(request, obj)
            form = ModelForm(request.POST, request.FILES, instance=obj)
            new_obj = self.save_form(request, form, change=True)

            effects = list(new_obj.all_effects)

            if effects:
                context = dict(
                    obj=obj,
                    title=_('Are you sure'),
                    post=request.POST,
                    opts=self.model._meta,
                    media=self.media,
                    effects=effects
                )

                return TemplateResponse(
                    request, "admin/change_effects_confirmation.html", context
                )

        return super(StateMachineAdminMixin, self).changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        send_messages = request.POST.get('send_messages') == 'on'
        obj.save(send_messages=send_messages)

    def get_transition(self, instance, name, field_name):
        transitions = getattr(instance, field_name).all_transitions
        for transition in transitions:
            if transition.name == name:
                return transition

    def transition(self, request, pk, field_name, transition_name, send_messages=True):
        link = reverse(
            'admin:{}_{}_change'.format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            args=(pk, )
        )

        # perform actual check for change permission. using self.model
        permission = '{}.change_{}'.format(
            self.model._meta.app_label, self.model._meta.model_name
        )
        if not request.user.has_perm(permission):
            messages.error(request, 'Missing permission: {}'.format(permission))
            return HttpResponseRedirect(link)

        instance = self.model.objects.get(pk=pk)
        form = TransitionConfirmationForm(request.POST)

        state_machine = getattr(instance, field_name)
        transition = state_machine.transitions[transition_name]

        if 'confirm' in request.POST and request.POST['confirm']:
            if form.is_valid():
                send_messages = form.cleaned_data['send_messages']

                getattr(state_machine, transition_name)(
                    user=request.user,
                )
                instance.save(send_messages=send_messages)

                log_action(
                    instance,
                    request.user,
                    'Changed status to {}'.format(transition.target.value)
                )

                return HttpResponseRedirect(link)

        effects = []
        for effect in transition.effects:
            effects += effect(instance).all_effects()

        context = dict(
            self.admin_site.each_context(request),
            title=TransitionConfirmationForm.title,
            action=transition.field,
            opts=self.model._meta,
            obj=instance,
            pk=instance.pk,
            form=form,
            source=instance.status,
            effects=effects,
            target=transition.target.name,
        )

        return TemplateResponse(
            request, 'admin/change_effects_confirmation.html', context
        )

    def get_urls(self):
        urls = super(StateMachineAdminMixin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/transition/(?P<field_name>.+)/(?P<transition_name>.+)$',
                self.admin_site.admin_view(self.transition),
                name='{}_{}_state_transition'.format(
                    self.model._meta.app_label, self.model._meta.model_name
                ),
            ),
        ]
        return custom_urls + urls


class StateMachineAdmin(StateMachineAdminMixin, admin.ModelAdmin):
    pass
