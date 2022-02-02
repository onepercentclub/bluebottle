from django.conf.urls import url

from bluebottle.segments.views import(
    SegmentList, SegmentDetail, SegmentTypeList, SegmentPublicDetail
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
        r'^(?P<pk>\d+)$',
        SegmentDetail.as_view(),
        name='segment-detail'
    ),

    url(
        r'^public/(?P<pk>\d+)/$',
        SegmentPublicDetail.as_view(),
        name='segment-public-detail'
    ),
]
