from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.models import File
from bluebottle.files.serializers import FileSerializer
from bluebottle.utils.views import CreateAPIView


class FileList(CreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
