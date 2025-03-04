from django.urls import re_path

from bluebottle.segments.views import (
    SegmentList, SegmentDetail, RelatedSegmentDetail, SegmentPublicDetail, SegmentTypeList,
    SegmentTypeDetail
)


urlpatterns = [
    re_path(
        r'^types/$',
        SegmentTypeList.as_view(),
        name='segment-type-list'
    ),
    re_path(
        r'^types/(?P<pk>\d+)$',
        SegmentTypeDetail.as_view(),
        name='segment-type-detail'
    ),
    re_path(
        r'^$',
        SegmentList.as_view(),
        name='segment-list'
    ),

    re_path(
        r'^types/(?P<segment_type>\d+)/segments$',
        RelatedSegmentDetail.as_view(),
        name='related-segment-detail'
    ),

    re_path(
        r'^(?P<pk>\d+)$',
        SegmentDetail.as_view(),
        name='segment-detail'
    ),

    re_path(
        r'^public/(?P<pk>\d+)$',
        SegmentPublicDetail.as_view(),
        name='segment-public-detail'
    ),
]
