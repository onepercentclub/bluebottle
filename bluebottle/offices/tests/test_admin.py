from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from bluebottle.geo.admin import LocationAdmin
from bluebottle.geo.models import Location
from bluebottle.initiatives.admin import InitiativeAdmin
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.admin import OfficeSubRegionAdmin, OfficeRegionAdmin
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion
from bluebottle.offices.tests.factories import OfficeSubRegionFactory, OfficeRegionFactory
from bluebottle.test.utils import BluebottleTestCase


class MockRequest(object):
    pass


class OfficeAdminTest(BluebottleTestCase):
    """
    Test Offices in admin
    """

    def setUp(self):
        super(OfficeAdminTest, self).setUp()
        self.africa = OfficeRegionFactory.create(name='Africa')
        self.europe = OfficeRegionFactory.create(name='Europe')
        self.bulgaria = OfficeSubRegionFactory.create(name='Bulgaria', region=self.europe)
        OfficeSubRegionFactory.create_batch(6, region=self.europe)
        self.ghana = OfficeSubRegionFactory.create(name='Ghana', region=self.africa)
        OfficeSubRegionFactory.create_batch(3, region=self.africa)
        self.location1 = Location.objects.create(
            name='Lyutidol',
            subregion=self.bulgaria
        )
        self.location2 = Location.objects.create(
            name='Sofia',
            subregion=self.bulgaria
        )
        self.location3 = Location.objects.create(
            name='Lozenets',
            subregion=self.bulgaria
        )
        self.location4 = Location.objects.create(
            name='Batak',
            subregion=self.bulgaria
        )
        self.location5 = Location.objects.create(
            name='Accra',
            subregion=self.ghana
        )
        self.site = AdminSite()
        self.location_admin = LocationAdmin(Location, self.site)
        self.subregion_admin = OfficeSubRegionAdmin(OfficeSubRegion, self.site)
        self.region_admin = OfficeRegionAdmin(OfficeRegion, self.site)
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        self.initiatives_url = reverse('admin:initiatives_initiative_changelist')
        self.activities_url = reverse('admin:activities_activity_changelist')
        InitiativeFactory.create(location=self.location1)
        InitiativeFactory.create_batch(3, location=self.location2)
        InitiativeFactory.create_batch(2, location=self.location3)
        InitiativeFactory.create_batch(4, location=self.location4)
        InitiativeFactory.create_batch(8, location=self.location5)

    def test_initiatives_link(self):
        initiatives_link = self.location_admin.initiatives(self.location1)
        self.assertTrue('>1<' in initiatives_link)
        self.assertTrue(
            '/en/admin/initiatives/initiative/?location__id__exact={}'.format(
                self.location1.id
            ) in initiatives_link
        )

        initiatives_link = self.location_admin.initiatives(self.location5)
        self.assertTrue('>8<' in initiatives_link)
        self.assertTrue(
            '/en/admin/initiatives/initiative/?location__id__exact={}'.format(
                self.location5.id
            ) in initiatives_link
        )

    def test_initiatives_link_regions_enabled(self):
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        initiatives_link = self.region_admin.initiatives(self.europe)
        self.assertTrue('>10<' in initiatives_link)
        self.assertTrue(
            '/en/admin/initiatives/initiative/?location__subregion__region__id__exact={}'.format(
                self.europe.id
            ) in initiatives_link
        )

        initiatives_link = self.region_admin.initiatives(self.africa)
        self.assertTrue('>8<' in initiatives_link)
        self.assertTrue(
            '/en/admin/initiatives/initiative/?location__subregion__region__id__exact={}'.format(
                self.africa.id
            ) in initiatives_link
        )

    def test_office_filters(self):
        request = MockRequest()
        filters = self.initiative_admin.get_list_filter(request)
        self.assertTrue('location' in filters)
        self.assertFalse('location__subregion_exact_id' in filters)
        self.assertFalse('location__subregion__region_exact_id' in filters)

    def test_office_filters_regions_enabled(self):
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        request = MockRequest()
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        filters = self.initiative_admin.get_list_filter(request)
        self.assertTrue('location__subregion' in filters)
        self.assertTrue('location__subregion__region' in filters)
