from bluebottle.projects.admin import ProjectAdmin
from bluebottle.test.utils import BluebottleTestCase


class ProjectsTestAdmin(BluebottleTestCase):
    def test_partner_field(self):
        self.failUnless('partner_organization'
                        in ProjectAdmin.fieldsets[0][1]['fields'])
