from bluebottle.projects.models import ProjectBudgetLine

from rest_framework import generics

from bluebottle.projects.serializers import ProjectBudgetLineSerializer, \
    ProjectDocumentSerializer
from bluebottle.projects.permissions import IsProjectOwner
from bluebottle.utils.utils import get_client_ip

from .models import ProjectDocument


class ManageProjectBudgetLineList(generics.ListCreateAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    paginate_by = 50
    permission_classes = (IsProjectOwner,)


class ManageProjectBudgetLineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (IsProjectOwner,)


class ManageProjectDocumentList(generics.ListCreateAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    paginate_by = 20
    filter = ('project',)

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)


class ManageProjectDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    paginate_by = 20
    filter = ('project',)

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)
