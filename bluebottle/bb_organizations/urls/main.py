from django.conf.urls import patterns, url

from ..views import RegistrationDocumentDownloadView

urlpatterns = patterns(
    '',
    url(r'^organizations/(?P<pk>\d+)/$', RegistrationDocumentDownloadView.as_view(),
        name='organization_registration_download'),
)
