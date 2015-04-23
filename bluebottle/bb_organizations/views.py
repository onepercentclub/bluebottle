import os

from bluebottle.utils.serializers import DefaultSerializerMixin, ManageSerializerMixin

from django.http import HttpResponseForbidden
from django.views.generic.detail import DetailView

from filetransfers.api import serve_file
from rest_framework import generics

from bluebottle.utils.utils import get_client_ip

from bluebottle.utils.model_dispatcher import get_organization_model, get_organizationdocument_model, get_organizationmember_model

from .permissions import IsOrganizationMember
from .serializers import OrganizationSerializer, ManageOrganizationSerializer, OrganizationDocumentSerializer

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()
DOCUMENT_MODEL = get_organizationdocument_model()


class OrganizationList(DefaultSerializerMixin, generics.ListAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = OrganizationSerializer
    paginate_by = 10


class OrganizationDetail(DefaultSerializerMixin, generics.RetrieveAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = OrganizationSerializer


class ManageOrganizationList(ManageSerializerMixin, generics.ListCreateAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = ManageOrganizationSerializer
    paginate_by = 10

    # Limit the view to only the organizations the current user is member of
    def get_queryset(self):
        org_members_ids = MEMBER_MODEL.objects.filter(user=self.request.user).values_list('id', flat=True).all()
        org_ids = self.model.objects.filter(members__in=org_members_ids).values_list('id', flat=True).all()
        queryset = super(ManageOrganizationList, self).get_queryset()
        queryset = queryset.filter(id__in=org_ids)
        return queryset

    def post_save(self, obj, created=False):
        if created:
            member = MEMBER_MODEL(user=self.request.user, organization=obj)
            member.save()


class ManageOrganizationDetail(ManageSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    model = ORGANIZATION_MODEL
    serializer_class = ManageOrganizationSerializer
    permission_classes = (IsOrganizationMember, )


class ManageOrganizationDocumentList(generics.ListCreateAPIView):
    model = DOCUMENT_MODEL
    serializer_class = OrganizationDocumentSerializer
    paginate_by = 20
    filter = ('organization', )

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)


class ManageOrganizationDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = DOCUMENT_MODEL
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
