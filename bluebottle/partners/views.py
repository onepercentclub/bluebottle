from bluebottle.clients.utils import tenant_url
from bluebottle.partners.serializers import PartnerOrganizationSerializer
from bluebottle.projects.models import PartnerOrganization, Project
from django.views.generic.list import ListView
from rest_framework import generics


# API view

class PartnerDetail(generics.RetrieveAPIView):
    model = PartnerOrganization
    serializer_class = PartnerOrganizationSerializer


# Django view

class MacroMicroListView(ListView):

    template_name = 'macromicro_list.html'
    model = Project
    queryset = Project.objects.filter(partner_organization__slug='macro_micro').filter(status__viewable=True)

    def render_to_response(self, context, **response_kwargs):
        return super(MacroMicroListView, self).render_to_response(
            context,
            mimetype='application/xml',
            **response_kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(MacroMicroListView, self).get_context_data(**kwargs)
        context['site'] = tenant_url()
        return context
