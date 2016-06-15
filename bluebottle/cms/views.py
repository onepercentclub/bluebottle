from django.views.generic.base import RedirectView
from rest_framework import generics, permissions

from bluebottle.cms.models import Page
from bluebottle.cms.serializers import PageSerializer


class PageList(generics.ListAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(live=True).all()


class PageDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(live=True).all()


class PageDraftDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    permission_classes = (permissions.IsAdminUser, )

    def get_queryset(self):
        return Page.objects.filter(live=True).all()

    def get_object(self):
        obj = super(PageDraftDetail, self).get_object()
        return obj.get_latest_revision_as_page()

class PreviewPage(RedirectView):

    def get_redirect_url(self):
        import ipdb; ipdb.set_trace()


class PreviewDraftPage(RedirectView):

    def get_redirect_url(self, page_id, **kwargs):
        return '/content-draft/' + page_id
