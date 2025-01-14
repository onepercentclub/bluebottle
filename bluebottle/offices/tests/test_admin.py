from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.urls import reverse

from bluebottle.activities.admin import ActivityAdmin
from bluebottle.activities.models import Activity
from bluebottle.geo.admin import LocationAdmin
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.admin import OfficeSubRegionAdmin, OfficeRegionAdmin
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion
from bluebottle.offices.tests.factories import OfficeSubRegionFactory, OfficeRegionFactory, LocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DeadlineActivityFactory


class MockRequest(object):
    pass


class OfficeAdminTest(BluebottleAdminTestCase):
    """
    Test Offices in admin
    """
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.africa = OfficeRegionFactory.create(name='Africa')
        self.europe = OfficeRegionFactory.create(name='Europe')
        self.bulgaria = OfficeSubRegionFactory.create(name='Bulgaria', region=self.europe)
        self.subregions = OfficeSubRegionFactory.create_batch(6, region=self.europe)
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
        self.activity_admin = ActivityAdmin(Activity, self.site)
        self.activities_url = reverse('admin:activities_activity_changelist')
        self.dateactivities_url = reverse('admin:time_based_dateactivity_changelist')
        DateActivityFactory.create(office_location=self.location1)
        DateActivityFactory.create_batch(3, office_location=self.location2)
        DateActivityFactory.create_batch(2, office_location=self.location3)
        DateActivityFactory.create_batch(4, office_location=self.location4)
        DateActivityFactory.create_batch(8, office_location=self.location5)

    def test_activities_link(self):
        activities_link = self.location_admin.activities(self.location1)
        self.assertEqual(
            f'<a href="/en/admin/activities/activity/?'
            f'office_location__id__exact={self.location1.id}">1</a>',
            activities_link
        )

        activities_link = self.location_admin.activities(self.location5)
        self.assertEqual(
            f'<a href="/en/admin/activities/activity/?'
            f'office_location__id__exact={self.location5.id}">8</a>',
            activities_link
        )

    def test_activities_link_regions_enabled(self):
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        activities_link = self.region_admin.activities(self.europe)
        self.assertEqual(
            f'<a href="/en/admin/activities/activity/?'
            f'office_location__subregion__region__id__exact={self.europe.id}">10</a>',
            activities_link
        )

        activities_link = self.region_admin.activities(self.africa)
        self.assertEqual(
            f'<a href="/en/admin/activities/activity/?'
            f'office_location__subregion__region__id__exact={self.africa.id}">8</a>',
            activities_link
        )

    def test_office_filters(self):
        request = MockRequest()
        request.user = BlueBottleUserFactory.create()
        filters = self.activity_admin.get_list_filter(request)
        self.assertTrue(('office_location', admin.RelatedOnlyFieldListFilter) in filters)
        self.assertFalse('office_location__subregion_exact_id' in filters)
        self.assertFalse('office_location__subregion__region_exact_id' in filters)

    def test_office_filters_regions_enabled(self):
        request = MockRequest()
        request.user = BlueBottleUserFactory.create()
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        filters = self.activity_admin.get_list_filter(request)
        self.assertTrue(('office_location', admin.RelatedOnlyFieldListFilter) in filters)
        self.assertTrue('office_location__subregion' in filters)
        self.assertTrue('office_location__subregion__region' in filters)

    def test_office_filters_region_manager(self):
        request = MockRequest()
        request.user = BlueBottleUserFactory.create(region_manager=self.subregions[0])
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        filters = self.activity_admin.get_list_filter(request)
        self.assertTrue(('office_location', admin.RelatedOnlyFieldListFilter) in filters)
        self.assertFalse('office_location__subregion_exact_id' in filters)
        self.assertFalse('office_location__subregion__region_exact_id' in filters)

    def test_office_admin(self):
        self.client.force_login(self.superuser)
        url = reverse('admin:geo_location_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Office group')
        self.assertContains(response, 'Office region')

    def test_office_admin_staff(self):
        self.client.force_login(self.staff_member)
        url = reverse('admin:geo_location_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Office group')
        self.assertContains(response, 'Office region')

    def test_activity_admin_region_filters(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.activities_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'office group')
        self.assertNotContains(response, 'office region')
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        response = self.client.get(self.activities_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'office group')
        self.assertContains(response, 'office region')
        response = self.client.get(self.activities_url, {
            'office_location__subregion__region__id__exact': self.location1.subregion.region.id,
            'office_location__subregion__id__exact': self.location1.subregion.id,
            'office_location__id__exact': self.location1.id,
        })
        self.assertEqual(response.status_code, 200)

    def test_dateactivity_admin_region_filters(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.dateactivities_url, {
            'office_location__subregion__region__id__exact': self.location1.subregion.region.id,
            'office_location__subregion__id__exact': self.location1.subregion.id,
            'office_location__id__exact': self.location1.id,
        })
        self.assertEqual(response.status_code, 200)

    def test_office_menu_for_staff(self):
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertFalse('Office group' in page.text)
        initiative_settings = InitiativePlatformSettings.objects.get()
        initiative_settings.enable_office_regions = True
        initiative_settings.save()
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertTrue('Office group' in page.text)


class RegionManagerAdminTest(BluebottleAdminTestCase):
    """
    Test Offices in admin
    """
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.subregion = OfficeSubRegionFactory.create()
        self.office = LocationFactory.create(subregion=self.subregion)
        self.region_manager = BlueBottleUserFactory.create(
            is_staff=True,
            region_manager=self.subregion
        )
        region_manager_group = Group.objects.get(name='Region Manager')
        region_manager_group.user_set.add(self.region_manager)
        self.app.set_user(self.region_manager)

    def test_menu(self):
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertFalse('Offices' in page.text)
        self.assertFalse('Groups' in page.text)
        self.assertFalse('Settings' in page.text)

    def test_activity_list(self):
        DeadlineActivityFactory.create()
        DeadlineActivityFactory.create(
            office_location=LocationFactory.create(
                subregion=OfficeSubRegionFactory.create()
            )
        )
        DeadlineActivityFactory.create(
            office_location=LocationFactory.create(
                subregion=self.subregion
            )
        )
        DeadlineActivityFactory.create(office_location=self.office)
        url = reverse('admin:activities_activity_changelist')
        page = self.app.get(url)

        self.assertTrue('2 Activities' in page.text, page.text)

    def test_initiative_list(self):
        owner = BlueBottleUserFactory.create(location=self.office)

        DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(owner=owner),
            office_location=LocationFactory.create()
        )
        DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(),
            office_location=self.office
        )
        DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(),
            office_location=LocationFactory.create()
        )

        url = reverse('admin:initiatives_initiative_changelist')
        page = self.app.get(url)
        self.assertTrue('2 Initiatives' in page.text)
