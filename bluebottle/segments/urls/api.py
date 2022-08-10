from django.conf.urls import url

from bluebottle.segments.views import (
    SegmentList, SegmentDetail, RelatedSegmentDetail, SegmentPublicDetail, SegmentTypeList
)


urlpatterns = [
    url(
        r'^types/$',
        SegmentTypeList.as_view(),
        name='segment-type-list'
    ),
    url(
        r'^$',
        SegmentList.as_view(),
        name='segment-list'
    ),

    url(
        r'^types/(?P<segment_type>\d+)/segments$',
        RelatedSegmentDetail.as_view(),
        name='related-segment-detail'
    ),

    url(
        r'^(?P<pk>\d+)$',
        SegmentDetail.as_view(),
        name='segment-detail'
    ),

    url(
        r'^public/(?P<pk>\d+)$',
        SegmentPublicDetail.as_view(),
        name='segment-public-detail'
    ),
]
