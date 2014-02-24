import os

from django.http import HttpResponseForbidden
from django.views.generic.detail import DetailView

from filetransfers.api import serve_file
from rest_framework import generics

from bluebottle.utils.utils import get_client_ip

from . import get_organization_model
from .models import OrganizationMember, OrganizationDocument
from .permissions import IsOrganizationMember
from .serializers import OrganizationSerializer, ManageOrganizationSerializer, OrganizationDocumentSerializer


ORGANIZATION_MODEL = get_organization_model()


class OrganizationList(generics.ListAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = OrganizationSerializer
    paginate_by = 10


class OrganizationDetail(generics.RetrieveAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = OrganizationSerializer


class ManageOrganizationList(generics.ListCreateAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = ManageOrganizationSerializer
    paginate_by = 10

    # Limit the view to only the organizations the current user is member of
    def get_queryset(self):
        return ORGANIZATION_MODEL.objects.filter(members__user=self.request.user)

    def post_save(self, obj, created=False):
        if created:
            member = OrganizationMember(organization=obj, user=self.request.user)
            member.save()


class ManageOrganizationDetail(generics.RetrieveUpdateAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = ManageOrganizationSerializer
    permission_classes = (IsOrganizationMember, )


class ManageOrganizationDocumentList(generics.ListCreateAPIView):
    model = OrganizationDocument
    serializer_class = OrganizationDocumentSerializer
    paginate_by = 20
    filter = ('organization', )

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)


class ManageOrganizationDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = OrganizationDocument
    serializer_class = OrganizationDocumentSerializer
    paginate_by = 20
    filter = ('organization', )

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)


#
# Non API views
#

# Download private documents
# OrganizationDocument handled by Bluebottle view

class RegistrationDocumentDownloadView(DetailView):
    model = ORGANIZATION_MODEL

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.is_staff:
            f = obj.registration.file
            file_name = os.path.basename(f. name)

            return serve_file(request, f, save_as=file_name)

        return HttpResponseForbidden()
