from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import (
    unquote,
)
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _


def get_obj_does_not_exist_redirect(self, request, opts, object_id):
    """
    Create a message informing the user that the object doesn't exist
    and return a redirect to the admin index page.
    """
    msg = _('%(name)s with ID “%(key)s” can’t be found. Perhaps you don’t have permission or maybe it was deleted?') % {
        'name': opts.verbose_name,
        'key': unquote(object_id),
    }
    self.message_user(request, msg, messages.WARNING)
    url = reverse('admin:index', current_app=self.admin_site.name)
    return HttpResponseRedirect(url)


ModelAdmin._get_obj_does_not_exist_redirect = get_obj_does_not_exist_redirect
