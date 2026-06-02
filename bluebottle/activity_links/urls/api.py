from django.urls import re_path

from bluebottle.activity_links.views import LinkedActivityImage

app_name = 'activity_links'

urlpatterns = [
    re_path(r'^image/(?P<pk>\d+)/(?P<size>\d+(x\d+)?)$', LinkedActivityImage.as_view(), name='image'),
]
