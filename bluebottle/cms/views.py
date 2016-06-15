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


class PreviewDraftPage(RedirectView):

    def get_redirect_url(self, page_id, **kwargs):
        # For convenience in local development
        if ':8000' in self.request.get_host():
            return 'http://{0}/en/content-draft/{1}/'.format(
                self.request.get_host().replace(':8000', ':4200'),
                page_id
            )

        return '/content-draft/' + page_id
