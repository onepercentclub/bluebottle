from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactRequestCreate(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            serializer.save(author=self.request.user)
        else:
            serializer.save()
