from django.conf.urls import patterns, url

from ..views import (
    WallPostDetail, TextWallPostList, MediaWallPostList, MediaWallPostPhotoList,
    MediaWallPostPhotoDetail, ReactionList, ReactionDetail, WallPostList)

urlpatterns = patterns(
    '',
    url(r'^$', WallPostList.as_view(), name='wallpost_list'),
    url(r'^(?P<pk>\d+)$', WallPostDetail.as_view(), name='wallpost_detail'),

    url(r'^textwallposts/$', TextWallPostList.as_view(), name='text_wallpost_list'),
    url(r'^mediawallposts/$', MediaWallPostList.as_view(), name='media_wallpost_list'),

    url(r'^photos/$', MediaWallPostPhotoList.as_view(), name='mediawallpost_photo_list'),
    url(r'^photos/(?P<pk>\d+)$', MediaWallPostPhotoDetail.as_view(), name='mediawallpost_photo_list'),

    url(r'^reactions/$', ReactionList.as_view(), name='wallpost_reaction_list'),
    url(r'^reactions/(?P<pk>\d+)$', ReactionDetail.as_view(), name='wallpost_reaction_detail')
)
