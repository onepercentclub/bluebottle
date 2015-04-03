from django.conf.urls import patterns
from surlex.dj import surl
from .views import AccountingOverviewView, AccountingDashboardView

urlpatterns = patterns('',
    surl(r'^overview/$', AccountingOverviewView.as_view(), name='admin-accounting-overview'),
    surl(r'^dashboard/$', AccountingDashboardView.as_view(), name='admin-accounting-dashboard'),
)

# NOTE:  multi admin urls are registered in the url root
