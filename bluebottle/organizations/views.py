from django.http import HttpResponseForbidden
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView


from bluebottle.organizations.models import Organization, OrganizationMember
from bluebottle.organizations.permissions import IsOrganizationMember
from bluebottle.organizations.serializers import OrganizationSerializer, ManageOrganizationSerializer


from filetransfers.api import serve_file
from rest_framework import generics
import os


class OrganizationList(generics.ListAPIView):
    model = Organization
    serializer_class = OrganizationSerializer
    paginate_by = 10


class OrganizationDetail(generics.RetrieveAPIView):
    model = Organization
    serializer_class = OrganizationSerializer


class ManageOrganizationList(generics.ListCreateAPIView):
    model = Organization
    serializer_class = ManageOrganizationSerializer
    paginate_by = 10

    # Limit the view to only the organizations the current user is member of
    def get_queryset(self):
        org_ids = OrganizationMember.objects.filter(user=self.request.user).values_list('organization_id', flat=True).all()
        queryset = super(ManageOrganizationList, self).get_queryset()
        queryset = queryset.filter(id__in=org_ids)
        return queryset

    def post_save(self, obj, created=False):
        if created:
            member = OrganizationMember(organization=obj, user=self.request.user)
            member.save()


class ManageOrganizationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Organization
    serializer_class = ManageOrganizationSerializer
    permission_classes = (IsOrganizationMember, )


# Non API views

# Download private documents

class RegistrationDocumentDownloadView(DetailView):
    model = Organization

    def get(self, request, pk):
        obj = self.get_object()
        if request.user.is_staff:
            f = obj.registration.file
            file_name = os.path.basename(f. name)
            return serve_file(request, f, save_as=file_name)
        return HttpResponseForbidden()
