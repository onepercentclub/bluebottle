from django.conf.urls import url

from ..views import ManageOrganizationContactList

urlpatterns = [
    url(r'^contacts', ManageOrganizationContactList.as_view(),
        name='manage_organization_contact_list')
]
