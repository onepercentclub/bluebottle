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


def admin_form(form_class, model, template):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, pk):
            obj = model.objects.get(pk=pk)
            # Try to initialize form with obj, fall back to no args if not supported
            try:
                form = form_class(obj=obj)
            except TypeError:
                form = form_class()
            if 'confirm' in request.POST and request.POST['confirm']:
                # Try to initialize form with POST data and obj, fall back to just POST if not supported
                try:
                    form = form_class(request.POST, obj=obj)
                except TypeError:
                    form = form_class(request.POST)
                if form.is_valid():
                    return func(self, request, obj, form)

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
