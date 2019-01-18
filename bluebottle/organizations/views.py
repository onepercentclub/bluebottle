import os

from django.http.response import HttpResponseForbidden
from django.views.generic.detail import DetailView

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework import filters

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.organizations.serializers import (OrganizationSerializer,
                                                  OrganizationContactSerializer)
from bluebottle.organizations.models import (
    Organization, OrganizationMember, OrganizationContact
)
from .permissions import IsContactOwner

from filetransfers.api import serve_file


class OrganizationContactList(generics.CreateAPIView):
    queryset = OrganizationContact
    serializer_class = OrganizationContactSerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OrganizationContactDetail(generics.UpdateAPIView):
    queryset = OrganizationContact
    serializer_class = OrganizationContactSerializer
    permission_classes = (IsContactOwner,)


class OrganizationDetail(generics.RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)


class OrganizationList(generics.ListCreateAPIView):
    serializer_class = OrganizationSerializer
    pagination_class = BluebottlePagination
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsAuthenticated,)
    search_fields = ('name',)

    def get_queryset(self):
        q = self.request.query_params

        # Only allow query if a search term is provided
        if ('search' in q and q['search'] != ''):
            return Organization.objects.all()

        return Organization.objects.none()

    def perform_create(self, serializer):
        organization = serializer.save()
        member = OrganizationMember(organization=organization, user=self.request.user)
        member.save()


#
# Non API views
#

# Download private documents

class RegistrationDocumentDownloadView(DetailView):
    queryset = Organization.objects.all()

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.is_staff:
            f = obj.registration.file
            file_name = os.path.basename(f.name)
            return serve_file(request, f, save_as=file_name)

        return HttpResponseForbidden()
