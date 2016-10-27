from ..views import WidgetView
from django.conf.urls import url

urlpatterns = [
    url('^$', WidgetView.as_view(), name='partner-widget'),
]
