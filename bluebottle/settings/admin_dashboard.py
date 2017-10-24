from django.utils.translation import ugettext_lazy as _

# Custom dashboard configuration
# ADMIN_TOOLS_INDEX_DASHBOARD = 'fluent_dashboard.dashboard.FluentIndexDashboard'
ADMIN_TOOLS_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'fluent_dashboard.dashboard.FluentAppIndexDashboard'
ADMIN_TOOLS_MENU = 'bluebottle.clients.admin_menu.AdminMenu'


# Further customize the dashboard
FLUENT_DASHBOARD_DEFAULT_MODULE = 'admin_tools.dashboard.modules.AppList'
FLUENT_DASHBOARD_APP_GROUPS = (
    (_('Site content'), {
        'models': [
            'bluebottle.pages.*',
            'bluebottle.news.*',
            'bluebottle.slides.*',
            'bluebottle.banners.*',
            'bluebottle.quotes.*',
            'bluebottle.terms.*',
            'bluebottle.contact.*',
            'bluebottle.statistics.*',
            'bluebottle.redirects.*',
            'bluebottle.cms.models.ResultPage'
        ],
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Projects'), {
        'models': (
            'bluebottle.projects.*',
            'bluebottle.bb_projects.*',
            'bluebottle.fundraisers.*',
            'bluebottle.categories.*',
            'bluebottle.organizations.*',
            'bluebottle.votes.*',
            'bluebottle.geo.models.Location',
            'bluebottle.rewards.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Tasks'), {
        'models': (
            'bluebottle.tasks.*',
            'bluebottle.bb_tasks.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Surveys'), {
        'models': (
            'bluebottle.surveys.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Wallposts'), {
        'models': (
            'bluebottle.wallposts.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Donations'), {
        'models': (
            'bluebottle.donations.*',
            'bluebottle.orders.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Monthly Donations'), {
        'models': (
            'bluebottle.recurring_donations.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Finances'), {
        'models': (
            'bluebottle.payments.*',
            'bluebottle.payments_docdata.*',
            'bluebottle.payments_logger.*',
            'bluebottle.payouts.*',
            'bluebottle.accounting.*',
            'bluebottle.journals.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Members'), {
        'models': (
            'django.contrib.auth.*',
            'registration.*',
            'bluebottle.members.*',
            'bluebottle.bb_accounts.*',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    (_('Settings'), {
        'models': (
            'bluebottle.cms.models.SitePlatformSettings',
            'bluebottle.projects.models.ProjectPlatformSettings',
        ),
        'module': 'fluent_dashboard.modules.AppIconList',
        'collapsible': False,
    }),
    # The '*' selector acts like a fallback for all other apps. This section mainly displays models
    # with tabular data that is rarely touched. The important models have an icon.
    (_('Applications'), {
        'models': ('*',),
        'module': FLUENT_DASHBOARD_DEFAULT_MODULE,
        'collapsible': False,
    }),
)

ADMIN_TOOLS_THEMING_CSS = 'css/admin/dashboard.css'
