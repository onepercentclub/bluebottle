from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.urls.base import reverse

from axes.utils import reset

from bluebottle.bluebottle_dashboard.forms import AxesCaptchaForm
from bluebottle.utils.utils import get_client_ip


@csrf_protect
def locked_out(request):
    if request.POST:
        form = AxesCaptchaForm(request.POST)
        if form.is_valid():
            ip = get_client_ip(request)
            reset(ip=ip)

            return HttpResponseRedirect(
                reverse('admin:login')
            )
    else:
        form = AxesCaptchaForm()

    return render(
        request,
        'admin/locked_out.html',
        dict(form=form),
    )
