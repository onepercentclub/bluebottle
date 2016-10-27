from surlex.dj import surl
from .views import (
    AccountingOverviewView, AccountingDashboardView, MultiTenantAccountingDashboardView,
    MultiTenantAccountingOverviewView)


urlpatterns = [
    surl(r'^overview/$', AccountingOverviewView.as_view(), name='admin-accounting-overview'),
    surl(r'^dashboard/$', AccountingDashboardView.as_view(), name='admin-accounting-dashboard'),
    surl(r'^multiadmin/$', MultiTenantAccountingDashboardView.as_view(), name='multiadmin-accounting-dashboard'),
    surl(r'^multiadmin/overview/$', MultiTenantAccountingOverviewView.as_view(), name='multiadmin-accounting-overview'),
]
