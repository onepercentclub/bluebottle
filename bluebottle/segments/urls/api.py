from django.urls import path

from bluebottle.segments.views import (
    SegmentList, SegmentDetail, RelatedSegmentDetail, SegmentPublicDetail, SegmentTypeList,
    SegmentTypeDetail
)


urlpatterns = [
    path(
        'types/',
        SegmentTypeList.as_view(),
        name='segment-type-list'
    ),
    path(
        'types/<int:pk>',
        SegmentTypeDetail.as_view(),
        name='segment-type-detail'
    ),
    path(
        '',
        SegmentList.as_view(),
        name='segment-list'
    ),

    path(
        'types/<int:segment_type>/segments',
        RelatedSegmentDetail.as_view(),
        name='related-segment-detail'
    ),

    path(
        '<int:pk>',
        SegmentDetail.as_view(),
        name='segment-detail'
    ),

    path(
        'public/<int:pk>',
        SegmentPublicDetail.as_view(),
        name='segment-public-detail'
    ),
]
