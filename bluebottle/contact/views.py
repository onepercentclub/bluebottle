from rest_framework import generics

from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactRequestCreate(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def pre_save(self, obj):
        if self.request.user.is_authenticated():
            obj.author = self.request.user
