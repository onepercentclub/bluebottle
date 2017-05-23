from django.contrib.admin.sites import AdminSite

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.geo.models import Location
from bluebottle.geo.admin import LocationAdmin


class LocationAdminTest(BluebottleTestCase):
    """ Tests for models in the geo app. """

    def setUp(self):
        super(LocationAdminTest, self).setUp()
        self.init_projects()
        self.location = Location.objects.create(
            name='Amsterdam',
            position='52.3702157,52.3702157'
        )
        self.site = AdminSite()
        self.admin = LocationAdmin(Location, self.site)
        ProjectFactory(location=self.location)

    def test_projects_link(self):
        """
        Test the numeric code validation.
        """
        projects_link = self.admin.projects(self.location)
        self.assertTrue('>1<' in projects_link)
        self.assertTrue(
            '/en/admin/projects/project/?location={}'.format(self.location.id) in projects_link
        )
