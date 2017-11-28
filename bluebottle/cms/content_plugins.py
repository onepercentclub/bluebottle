from django.utils.translation import ugettext_lazy as _

from fluent_contents.extensions import plugin_pool, ContentPlugin

from bluebottle.cms.admin import (
    QuoteInline, StatInline, SlideInline, StepInline, LogoInline, LinkInline,
    GreetingInline
)
from bluebottle.cms.models import (
    QuotesContent, StatsContent, SurveyContent, ProjectsContent,
    ProjectImagesContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent, TasksContent, StepsContent, SlidesContent,
    CategoriesContent, LocationsContent, LogosContent,
    LinksContent, WelcomeContent
)


class CMSContentPlugin(ContentPlugin):
    admin_form_template = 'admin/cms/content_item.html'

    class Media:
        css = {
            "all": ('admin/css/forms-nested.css', )
        }
        js = (
            'admin/js/inlines-nested.js',
            'js/csrf.js',
            'adminsortable/js/jquery-ui-django-admin.min.js',
            'adminsortable/js/admin.sortable.stacked.inlines.js'
        )


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


@plugin_pool.register
class SlidesBlockPlugin(CMSContentPlugin):
    model = SlidesContent
    inlines = [SlideInline]

    category = _('Homepage')


@plugin_pool.register
class StepsBlockPlugin(CMSContentPlugin):
    model = StepsContent
    inlines = [StepInline]
    category = _('Homepage')


@plugin_pool.register
class CategoriesBlockPlugin(CMSContentPlugin):
    model = CategoriesContent
    raw_id_fields = ('categories', )
    category = _('Homepage')


@plugin_pool.register
class LocationsBlockPlugin(CMSContentPlugin):
    model = LocationsContent
    raw_id_fields = ('locations', )
    category = _('Homepage')


@plugin_pool.register
class LogosBlockPlugin(CMSContentPlugin):
    model = LogosContent
    inlines = [LogoInline]
    category = _('Homepage')


@plugin_pool.register
class LinksBlockPlugin(CMSContentPlugin):
    model = LinksContent
    inlines = [LinkInline]
    category = _('Homepage')


@plugin_pool.register
class WelcomeBlockPlugin(CMSContentPlugin):
    model = WelcomeContent
    inlines = [GreetingInline]
    category = _('Homepage')
