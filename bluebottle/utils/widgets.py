from __future__ import unicode_literals

from urlparse import urlparse

from django.contrib.admin.widgets import AdminURLFieldWidget


class SecureAdminURLFieldWidget(AdminURLFieldWidget):
    def render(self, name, value, attrs=None):
        if value and urlparse(value).scheme not in ('http', 'https', ):
            return super(AdminURLFieldWidget, self).render(name, value, attrs)
        else:
            return super(SecureAdminURLFieldWidget, self).render(name, value, attrs)
