from django.conf.urls import url

from ..views import RegistrationDocumentDownloadView

urlpatterns = [
    url(r'^organizations/(?P<pk>\d+)/$',
        RegistrationDocumentDownloadView.as_view(),
        name='organization_registration_download'),
]
