from builtins import object
from builtins import str
from collections import defaultdict

from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.notifications.effects import BaseNotificationEffect
from bluebottle.utils.forms import TransitionConfirmationForm


def log_action(obj, user, change_message='Changed', action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=change_message
    )


def get_effects(effects):
    displayed_effects = [effect for effect in effects if effect.display]
    displayed_effects.sort(key=lambda x: x.__class__.__name__)
    grouped_effects = defaultdict(list)

    for effect in displayed_effects:
        grouped_effects[(effect.__class__, effect.instance.__class__)].append(effect)

    return [cls.render(grouped) for (cls, instance_cls), grouped in list(grouped_effects.items())]


class StateMachineAdminMixin(object):
    form = StateMachineModelForm

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Determines the HttpResponse for the change_view stage.
        """
        if (
            object_id and
            request.method == 'POST' and
            not request.POST.get('post', False) and
            '_saveasnew' not in request.POST
        ):
            obj = self.model.objects.get(pk=object_id)
            ModelForm = self.get_form(request, obj)
            form = ModelForm(request.POST, request.FILES, instance=obj)
            # If there are form errors, then don't go to the confirm page yet.
            if not form.is_valid():
                return super(StateMachineAdminMixin, self).changeform_view(request, object_id, form_url, extra_context)

            new_obj = self.save_form(request, form, change=True)

            send_messages = request.POST.get('enable_messages') == 'on'
            effects = new_obj.execute_triggers(user=request.user, send_messages=send_messages)

            formsets, inline_instances = self._create_formsets(request, new_obj, change=True)

            for formset in formsets:
                for form in formset:
                    if isinstance(form.instance, TriggerMixin):
                        if form.is_valid():
                            form.save(commit=False)
                            if form.instance:
                                effects += form.instance.execute_triggers(
                                    user=request.user,
                                    send_messages=send_messages
                                )
            rendered_effects = get_effects(effects)
            if rendered_effects:

                cancel_link = reverse(
                    'admin:{}_{}_change'.format(
                        self.model._meta.app_label, self.model._meta.model_name
                    ),
                    args=(object_id, )
                )
                action_text = ' and '.join(
                    str(trigger.title) for trigger in obj._triggers
                ) or _('perform changes')

                context = dict(
                    obj=obj,
                    title=_('Are you sure'),
                    cancel_url=cancel_link,
                    post=request.POST,
                    opts=self.model._meta,
                    action_text=action_text,
                    media=self.media,
                    has_notifications=any(
                        isinstance(effect, BaseNotificationEffect)
                        for effect in effects
                    ),
                    effects=rendered_effects
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
        obj.execute_triggers(user=request.user, send_messages=send_messages)
        obj.save()

    def save_formset(self, request, form, formset, change):
        """
        Given an inline formset save it to the database.
        """
        send_messages = request.POST.get('send_messages') == 'on'
        for form in formset.forms:
            if isinstance(form.instance, TriggerMixin):
                form.instance.execute_triggers(user=request.user, send_messages=send_messages)

        formset.save()

    def get_transition(self, instance, name, field_name):
        transitions = getattr(instance, field_name).all_transitions
        for transition in transitions:
            if transition.name == name:
                return transition

    def transition(self, request, pk, field_name, transition_name):
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

        if transition not in state_machine.possible_transitions():
            messages.error(request, 'Transition not possible: {}'.format(transition.name))
            return HttpResponseRedirect(link)

        if 'confirm' in request.POST and request.POST['confirm']:
            if form.is_valid():
                send_messages = form.cleaned_data['send_messages']
                getattr(state_machine, transition_name)(
                    user=request.user
                )
                try:
                    instance.execute_triggers(user=request.user, send_messages=send_messages)
                    instance.save()
                except TransitionNotPossible as e:
                    messages.warning(request, 'Effect failed: {}'.format(e))

                log_action(
                    instance,
                    request.user,
                    'Changed status to {}'.format(transition.target.value)
                )

                return HttpResponseRedirect(link)

        getattr(state_machine, transition_name)()
        effects = instance.execute_triggers(user=request.user)
        rendered_effects = get_effects(effects)
        cancel_link = reverse(
            'admin:{}_{}_change'.format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            args=(pk, )
        )
        action_text = "change the status to {}".format(transition.target.name)

        context = dict(
            self.admin_site.each_context(request),
            title=TransitionConfirmationForm.title,
            action=transition.field,
            opts=self.model._meta,
            cancel_url=cancel_link,
            obj=instance,
            pk=instance.pk,
            transition=transition,
            action_text=action_text,
            form=form,
            has_notifications=any(
                isinstance(effect, BaseNotificationEffect)
                for effect in effects
            ),
            source=instance.status,
            effects=rendered_effects,
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
            )
        ]
        return custom_urls + urls

    def state_name(self, obj):
        if hasattr(self, 'child_models'):
            obj = obj.get_real_instance()

        if obj.states.current_state:
            return obj.states.current_state.name

    state_name.short_description = _('status')


class StateMachineAdmin(StateMachineAdminMixin, admin.ModelAdmin):
    pass


class StateMachineFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        if hasattr(model_admin, 'child_models'):
            states = []
            for model in model_admin.child_models:
                states += list(model._state_machines['states'].states.items())
        else:
            states = list(model_admin.model._state_machines['states'].states.items())

        return set((status, state.name) for (status, state) in states)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                status=self.value()
            )
        else:
            return queryset
