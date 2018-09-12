from django.conf.urls import url

from bluebottle.wallposts.views import MediaWallpostDetail, TextWallpostDetail
from ..views import (
    WallpostDetail, TextWallpostList, MediaWallpostList, MediaWallpostPhotoList,
    MediaWallpostPhotoDetail, ReactionList, ReactionDetail, WallpostList)

urlpatterns = [
    url(r'^$', WallpostList.as_view(), name='wallpost_list'),
    url(r'^(?P<pk>\d+)$', WallpostDetail.as_view(), name='wallpost_detail'),

    url(r'^textwallposts/$', TextWallpostList.as_view(),
        name='text_wallpost_list'),
    url(r'^textwallposts/(?P<pk>\d+)$', TextWallpostDetail.as_view(),
        name='text_wallpost_detail'),

    url(r'^mediawallposts/$', MediaWallpostList.as_view(),
        name='media_wallpost_list'),
    url(r'^mediawallposts/(?P<pk>\d+)$', MediaWallpostDetail.as_view(),
        name='media_wallpost_detail'),

    url(r'^photos/$', MediaWallpostPhotoList.as_view(),
        name='mediawallpost_photo_list'),
    url(r'^photos/(?P<pk>\d+)$', MediaWallpostPhotoDetail.as_view(),
        name='mediawallpost_photo_list'),

    url(r'^reactions/$', ReactionList.as_view(), name='wallpost_reaction_list'),
    url(r'^reactions/(?P<pk>\d+)$', ReactionDetail.as_view(),
        name='wallpost_reaction_detail')
]
