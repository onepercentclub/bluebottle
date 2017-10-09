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


@plugin_pool.register
class StatsBlockPlugin(CMSContentPlugin):
    model = StatsContent
    inlines = [StatInline]


@plugin_pool.register
class SurveyBlockPlugin(CMSContentPlugin):
    model = SurveyContent


@plugin_pool.register
class ProjectsBlockPlugin(CMSContentPlugin):
    model = ProjectsContent


@plugin_pool.register
class ProjectImagesBlockPlugin(CMSContentPlugin):
    model = ProjectImagesContent


@plugin_pool.register
class ShareResultsBlockPlugin(CMSContentPlugin):
    model = ShareResultsContent


@plugin_pool.register
class ProjectMapBlockPlugin(CMSContentPlugin):
    model = ProjectsMapContent


@plugin_pool.register
class SupporterTotalBlockPlugin(CMSContentPlugin):
    model = SupporterTotalContent


@plugin_pool.register
class TasksBlockPlugin(CMSContentPlugin):
    model = TasksContent
    raw_id_fields = ('tasks', )
