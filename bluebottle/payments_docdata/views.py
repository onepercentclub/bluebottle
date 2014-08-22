from django.http import HttpResponse
from django.views.generic import View


class PaymentStatusUpdateView(View):

    def get(self, request):
        print request.DATA


        return HttpResponse('success')
