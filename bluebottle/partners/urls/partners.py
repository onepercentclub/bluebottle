from django.conf.urls import patterns, url

from ..views import MacroMicroListView

urlpatterns = patterns('', url('macromicro/xml',
                               MacroMicroListView.as_view(),
                               name='macromicro-list'))
