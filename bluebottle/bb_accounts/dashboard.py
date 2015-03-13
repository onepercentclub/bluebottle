from admin_tools.dashboard.modules import DashboardModule
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

BB_USER_MODEL = get_user_model()


class UserModule(DashboardModule):
    """
    Generic project module for the django admin tools dashboard.
    """
    title = _('Users')
    template = 'admin_tools/dashboard/user_module.html'
    limit = 10

    def __init__(self, title=None, limit=10, filter_kwargs=None, order_by=None, **kwargs):
        if order_by is None:
            order_by = '-pk'
        self.order_by = order_by

        if filter_kwargs is None:
            filter_kwargs = {}
        self.filter_kwargs = filter_kwargs

        kwargs.update({'limit': limit})
        super(UserModule, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        qs = BB_USER_MODEL.objects.filter(**self.filter_kwargs).order_by(self.order_by)

        self.children = qs[:self.limit]

        for c in self.children:
            c.admin_url = reverse('admin:{0}_{1}_change'.format(
                BB_USER_MODEL._meta.app_label, BB_USER_MODEL._meta.module_name), args=(c.pk,))

        if not len(self.children):
            self.pre_content = _('No users found.')
        self._initialized = True

    @property
    def post_content(self):
        url = reverse('admin:{0}_{1}_changelist'.format(BB_USER_MODEL._meta.app_label, BB_USER_MODEL._meta.module_name))
        return mark_safe('<a href="{0}">{1}</a>'.format(url, ugettext('View all users')))
