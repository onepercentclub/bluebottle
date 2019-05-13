import functools

from django.contrib.admin import helpers
from django.template.response import TemplateResponse


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
            if 'confirm' in request.POST and request.POST['confirm']:
                form = form_class(request.POST)
                if form.is_valid():
                    return func(self, request, obj, target,
                                send_messages=form.cleaned_data['send_messages'])

            messages = []
            for message_list in [message(obj).get_messages() for message in getattr(obj, target).messages]:
                messages += message_list

            context = dict(
                self.admin_site.each_context(request),
                title=form_class.title,
                action=func.__name__,
                opts=self.model._meta,
                obj=obj,
                pk=pk,
                form=form,
                source=obj.status,
                notifications=messages,
                target=target,
            )

            return TemplateResponse(request, template, context)

        wrapper.short_description = form_class.title

        return wrapper

    return decorator
