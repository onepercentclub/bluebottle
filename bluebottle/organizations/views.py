import os

from django.http.response import HttpResponseForbidden
from django.views.generic.detail import DetailView

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from bluebottle.organizations.models import Organization
from bluebottle.organizations.serializers import ManageOrganizationContactSerializer

from filetransfers.api import serve_file


# Non API views
# Download private documents

class RegistrationDocumentDownloadView(DetailView):
    queryset = Organization.objects.all()

    def get(self, request, pk):
        obj = self.get_object()
        if request.user.is_staff:
            f = obj.registration.file
            file_name = os.path.basename(f.name)
            return serve_file(request, f, save_as=file_name)
        return HttpResponseForbidden()


class ManageOrganizationContactList(generics.CreateAPIView):
    serializer_class = ManageOrganizationContactSerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
