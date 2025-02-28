from django.urls import re_path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse


class AdminMergeMixin:

    def get_urls(self):
        urls = super().get_urls()

        extra_urls = [
            re_path(
                r"^(?P<pk>\d+)/merge/$",
                self.admin_site.admin_view(self.merge),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_merge",
            ),
        ]
        return extra_urls + urls

    def merge(self, request, pk, *args, **kwargs):
        obj = self.model.objects.get(pk=pk)
        if request.method == "POST":
            form = self.merge_form(data=request.POST, obj=obj)
            if form.is_valid():
                data = form.cleaned_data
                data["to"].merge(obj)
                change_url = reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                    args=(data["to"].pk,),
                )
                return HttpResponseRedirect(change_url)

        context = {
            "opts": self.model._meta,
            "obj": obj,
            "form": self.merge_form(obj=obj),
        }
        return TemplateResponse(request, "admin/merge.html", context)
