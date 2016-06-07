import os

from django.http import HttpResponseForbidden
from django.views.generic.detail import DetailView

from filetransfers.api import serve_file
from rest_framework import generics

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.organizations.serializers import OrganizationSerializer, \
    ManageOrganizationSerializer
from bluebottle.organizations.models import Organization, OrganizationMember

from .permissions import IsOrganizationMember


class OrganizationList(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = BluebottlePagination


class OrganizationDetail(generics.RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class ManageOrganizationList(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = ManageOrganizationSerializer
    pagination_class = BluebottlePagination

    # Limit the view to only the organizations the current user is member of
    def get_queryset(self):
        org_members_ids = OrganizationMember.objects.filter(
            user=self.request.user).values_list('id', flat=True).all()
        org_ids = self.queryset.filter(
            members__in=org_members_ids).values_list('id', flat=True).all()
        queryset = super(ManageOrganizationList, self).get_queryset()
        queryset = queryset.filter(id__in=org_ids)
        return queryset

    def post_save(self, obj, created=False):
        if created:
            member = OrganizationMember(user=self.request.user, organization=obj)
            member.save()


class ManageOrganizationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = ManageOrganizationSerializer
    permission_classes = (IsOrganizationMember,)


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
