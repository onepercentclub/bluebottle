from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.forms.models import modelform_factory

from bluebottle.projects.admin import (
    LocationFilter, ProjectReviewerFilter, ProjectAdmin, ProjectAdminForm,
    ReviewerWidget
)
from bluebottle.projects.models import Project

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


# RequestFactory used for integration tests.
factory = RequestFactory()


class LocationFilterTest(BluebottleTestCase):
    """
    Test project admin location filter
    """

    def setUp(self):
        super(LocationFilterTest, self).setUp()
        self.init_projects()

        amsterdam = LocationFactory.create(name='Amsterdam')
        rotterdam = LocationFactory.create(name='Rotterdam')
        durgerdam = LocationFactory.create(name='Durgerdam')
        self.locations = [amsterdam, rotterdam, durgerdam]

        self.user = BlueBottleUserFactory.create(location=amsterdam)
        self.amsterdam_project = ProjectFactory.create(
            title='Project in Amsterdam',
            location=amsterdam
        )
        ProjectFactory.create(
            title='Project in Rotterdam',
            location=rotterdam
        )
        ProjectFactory.create(
            title='Project in Durgerdam',
            location=durgerdam
        )
        self.admin = ProjectAdmin(Project, AdminSite())

        self.filter = LocationFilter(None, {'location': amsterdam.pk}, Project, self.admin)

    def testLookup(self):
        request = factory.get('/', user=None)

        lookups = self.filter.lookups(request, self.admin)
        self.assertEqual(
            set(location.name for location in self.locations),
            set(lookup[1] for lookup in lookups)
        )

    def testLookupUser(self):
        request = factory.get('/')
        request.user = self.user
        lookups = self.filter.lookups(request, self.admin)

        self.assertEqual(len(lookups), 4)
        self.assertEqual(
            lookups[0],
            (request.user.location.id, u'My location (Amsterdam)')
        )

    def test_filter(self):
        queryset = self.filter.queryset(None, Project.objects.all())
        self.assertEqual(queryset.get(), self.amsterdam_project)


class ProjectReviewerFilterTest(BluebottleTestCase):
    """
    Test project reviewer filter
    """

    def setUp(self):
        super(ProjectReviewerFilterTest, self).setUp()
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.project_with_reviewer = ProjectFactory.create(
            reviewer=self.user
        )
        self.project = ProjectFactory.create(
        )

        self.request = factory.get('/')
        self.request.user = self.user
        self.admin = ProjectAdmin(Project, AdminSite())

    def test_filter(self):
        filter = ProjectReviewerFilter(None, {'reviewer': True}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(queryset.get(), self.project_with_reviewer)

    def test_filter_false(self):
        filter = ProjectReviewerFilter(None, {'reviewer': False}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(len(queryset), len(Project.objects.all()))


class ProjectAdminFormTest(BluebottleTestCase):
    def setUp(self):
        super(ProjectAdminFormTest, self).setUp()
        self.init_projects()
        self.form = modelform_factory(Project, ProjectAdminForm, exclude=[])()

    def test_reviewer_field(self):
        widget = self.form.fields['reviewer'].widget
        self.assertTrue(
            isinstance(widget, ReviewerWidget)
        )
        parameters = widget.url_parameters()
        self.assertTrue(parameters['is_staff'], True)
