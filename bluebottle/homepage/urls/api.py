from bluebottle.homepage.views import HomePageDetail
from surlex.dj import surl

urlpatterns = [
    surl(r'^<language:s>$', HomePageDetail.as_view(),
         name='stats'),
]
