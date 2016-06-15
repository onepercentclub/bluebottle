from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from bluebottle.cms.views import project_chooser, project_chosen

urlpatterns = [
    url(r'^chooser/$', project_chooser, name='project_chooser'),
    url(r'^chooser/(\d+)/$', project_chosen, name='project_chosen')
]

