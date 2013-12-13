from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http.response import Http404
from django.shortcuts import get_list_or_404, get_object_or_404
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from rest_framework import generics

from .models import ContactMessage, Page
from .serializers import ContactMessageSerializer, PageSerializer


class PageList(generics.ListAPIView):
    model = Page
    serializer_class = PageSerializer
    paginate_by = 10
    filter_fields = ('language', 'slug')

    def get_queryset(self):
        qs = super(PageList, self).get_queryset()
        qs = qs.filter(status=Page.PageStatus.published)
        qs = qs.filter(publication_date__lte=now)
        qs = qs.filter(Q(publication_end_date__gte=now) |
                       Q(publication_end_date__isnull=True))
        return qs


class PageDetail(generics.RetrieveAPIView):
    model = Page
    serializer_class = PageSerializer

    def get_queryset(self):
        qs = super(PageDetail, self).get_queryset()
        qs = qs.filter(status=Page.PageStatus.published)
        qs = qs.filter(publication_date__lte=now)
        qs = qs.filter(Q(publication_end_date__gte=now) |
                       Q(publication_end_date__isnull=True))
        return qs

    def get_object(self, queryset=None):
        qs = self.get_queryset()
        qs = qs.filter(slug=self.kwargs['slug'])
        qs = get_list_or_404(qs, slug=self.kwargs['slug'])
        obj = get_object_or_404(qs, language=self.kwargs['language'])

        return obj


class ContactRequestCreate(generics.CreateAPIView):
    model = ContactMessage
    serializer_class = ContactMessageSerializer

    def pre_save(self, obj):
        if self.request.user.is_authenticated():
            obj.author = self.request.user
