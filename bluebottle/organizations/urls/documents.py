from surlex.dj import surl
from ..views import RegistrationDocumentDownloadView

urlpatterns = [
    surl(r'^organizations/<pk:#>/$',
         RegistrationDocumentDownloadView.as_view(),
         name='organization-registration-download'),
]
