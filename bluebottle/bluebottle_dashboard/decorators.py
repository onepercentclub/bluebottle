import functools

from django.contrib.messages import error
from django.contrib.admin import helpers
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import loader
from django.template.response import TemplateResponse
from django.forms.models import model_to_dict
from django.utils.module_loading import import_string


def confirmation_form(form_class, model, template):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, pk):
            form = form_class()
            obj = model.objects.get(pk=pk)
            if 'confirm' in request.POST and request.POST['confirm']:
                form = form_class(request.POST)
                if form.is_valid():
                    return func(self, request, obj)

            context = dict(
                self.admin_site.each_context(request),
                title=form_class.title,
                action=func.__name__,
                opts=self.model._meta,
                obj=obj,
                pk=pk,
                form=form,
                action_checkbox_name=helpers.ACTION_CHECKBOX_NAME
            )

            return TemplateResponse(request, template, context)

        wrapper.short_description = form_class.title

        return wrapper

    return decorator


def transition_confirmation_form(form_class, template):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, pk, target):
            form = form_class()
            model = self.model
            obj = model.objects.get(pk=pk)
            transition = getattr(obj, target)

            if hasattr(transition, 'form'):

                form = import_string(transition.form)(data=model_to_dict(obj))
                if form.errors:
                    errors = loader.get_template('admin/transition_errors.html').render(
                        {'errors': dict((form.fields[field].label, errors) for field, errors in form.errors.items())}
                    )
                    error(request, errors)
                    object_url = 'admin:{}_{}_change'.format(self.model._meta.app_label, self.model._meta.model_name)
                    return HttpResponseRedirect(
                        reverse(object_url, args=(obj.pk, ))
                    )

            if 'confirm' in request.POST and request.POST['confirm']:
                form = form_class(request.POST)
                if form.is_valid():
                    return func(self, request, obj, target,
                                send_messages=form.cleaned_data['send_messages'])

            messages = []
            for message_list in [message(obj).get_messages() for message in transition.messages]:
                messages += message_list

            context = dict(
                self.admin_site.each_context(request),
                title=form_class.title,
                action=func.__name__,
                opts=self.model._meta,
                obj=obj,
                pk=pk,
                form=form,
                source=obj.review_status,
                notifications=messages,
                target=target,
            )

            return TemplateResponse(request, template, context)

        wrapper.short_description = form_class.title

        return wrapper

    return decorator
