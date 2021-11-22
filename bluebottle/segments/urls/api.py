from django.conf.urls import url

from bluebottle.segments.views import SegmentList, SegmentDetail, SegmentTypeList


urlpatterns = [
    url(
        r'^types/$',
        SegmentTypeList.as_view(),
        name='segment-type-list'
    ),
    url(
        r'^segments/$',
        SegmentList.as_view(),
        name='segment-list'
    ),

    url(
        r'^segments/(?P<pk>\d+)$',
        SegmentDetail.as_view(),
        name='segment-detail'
    ),
]
