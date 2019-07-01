from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _


class PayoutAccountProjectLinkMixin(object):

    def project_links(self, obj):
        return format_html(", ".join([
            format_html(
                u"<a href='{}'>{}</a>",
                reverse('admin:projects_project_change', args=(p.id, )),
                p.title
            ) for p in obj.projects
        ]))
    project_links.short_description = _('Projects')
