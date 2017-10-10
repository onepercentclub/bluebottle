from django.utils.translation import ugettext_lazy as _

from fluent_contents.extensions import plugin_pool, ContentPlugin

from bluebottle.cms.admin import QuoteInline, StatInline
from bluebottle.cms.models import (
    QuotesContent, StatsContent, SurveyContent, ProjectsContent,
    ProjectImagesContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent, TasksContent
)


class CMSContentPlugin(ContentPlugin):
    admin_form_template = 'admin/cms/content_item.html'


@plugin_pool.register
class QuotesBlockPlugin(CMSContentPlugin):
    model = QuotesContent
    inlines = [QuoteInline]
    category = _('Content')


@plugin_pool.register
class StatsBlockPlugin(CMSContentPlugin):
    model = StatsContent
    inlines = [StatInline]
    category = _('Stats')


@plugin_pool.register
class SurveyBlockPlugin(CMSContentPlugin):
    model = SurveyContent
    category = _('Results')


@plugin_pool.register
class ProjectsBlockPlugin(CMSContentPlugin):
    model = ProjectsContent
    raw_id_fields = ('projects', )
    category = _('Projects')


@plugin_pool.register
class ProjectImagesBlockPlugin(CMSContentPlugin):
    model = ProjectImagesContent
    category = _('Projects')


@plugin_pool.register
class ShareResultsBlockPlugin(CMSContentPlugin):
    model = ShareResultsContent
    category = _('Results')


@plugin_pool.register
class ProjectMapBlockPlugin(CMSContentPlugin):
    model = ProjectsMapContent
    category = _('Projects')


@plugin_pool.register
class SupporterTotalBlockPlugin(CMSContentPlugin):
    model = SupporterTotalContent
    category = _('Stats')


@plugin_pool.register
class TasksBlockPlugin(CMSContentPlugin):
    model = TasksContent
    raw_id_fields = ('tasks', )
    category = _('Tasks')
