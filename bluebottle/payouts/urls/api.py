from django.conf.urls import url

from bluebottle.payouts.views import ManagePayoutDocumentList, ManagePayoutDocumentDetail


urlpatterns = [
    url(r'^documents/manage/$', ManagePayoutDocumentList.as_view(), name='manage_payout_document_list'),
    url(r'^documents/manage/(?P<pk>\d+)$', ManagePayoutDocumentDetail.as_view(),
        name='manage_payout_document_detail'),

]
