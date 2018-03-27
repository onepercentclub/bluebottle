from django.utils.translation import ugettext_lazy as _


JET_INDEX_DASHBOARD = 'bluebottle.bluebottle_dashboard.dashboard.CustomIndexDashboard'
JET_APP_INDEX_DASHBOARD = 'bluebottle.bluebottle_dashboard.dashboard.CustomAppIndexDashboard'

JET_DEFAULT_THEME = 'light-gray'

JET_SIDE_MENU_ITEMS = [  # A list of application or custom item dicts
    {
        'label': _('Projects'),
        'app_label': 'projects',
        'permissions': ['projects.change_project'],
        'items': [
            {'name': 'projects.project', 'permissions': ['projects.project']},
            {'name': 'categories.category'},
            {'name': 'fundraisers.fundraiser'},
            {'name': 'bb_projects.projectphase'},
            {'name': 'bb_projects.projecttheme'},
            {'name': 'organizations.organization'},
            {'name': 'geo.location'},
        ]
    },
    {
        'label': _('Users'),
        'app_label': 'members',
        'permissions': ['members.change_member'],
        'items': [
            {'name': 'members.member'},
            {'name': 'auth.group'},
        ]
    },
    {
        'label': _('Volunteering'),
        'app_label': 'tasks',
        'permissions': ['tasks.change_task'],
        'items': [
            {'name': 'tasks.task'},
            {'name': 'tasks.taskmember'},
            {'name': 'tasks.skill'},
        ]
    },
    {
        'label': _('Giving'), 'items': [
            {'name': 'donations.donation'},
            {'name': 'orders.order'},
            {'name': 'recurring_donations.monthlybatch'},
            {'name': 'recurring_donations.monthlydonation'},
            {'name': 'recurring_donations.monthlydonor'},
            {'name': 'recurring_donations.monthlyorder'},
            {'name': 'payments.orderpayment'},
            {'name': 'payments.payment'},
        ]
    },
    {
        'label': _('Content'),
        'items': [
            {'name': 'pages.page'},
            {
                'name': 'news.newsitem',
                'label': _('News')
            },
            {
                'name': 'cms.homepage',
                'label': _('Homepage')
            },
            {'name': 'slides.slide'},
            {
                'name': 'cms.resultpage',
                'label': _('Result page')
            },
            {
                'name': 'cms.sitelinks',
                'label': _('Menu')
            },
            {'name': 'redirects.redirect'},

        ]
    },
    {
        'label': _('Wall Posts'),
        'permissions': ['wallposts.wallpost'],
        'items': [
            {
                'name': 'wallposts.wallpost',
            },
            {
                'url': '/admin/wallposts/mediawallpost/',
                'label': _('Media wall posts')
            },
            {
                'name': 'wallposts.reaction'
            },
        ]
    },
    {
        'label': _('Analytics'),
        'app_label': 'looker',
        'url': {'type': 'app', 'app_label': 'looker'},
        'items': [
            {
                'label': _('Manage Dashboards'),
                'name': 'looker.lookerembed',
            },
        ]
    },
    {
        'label': _('Settings'),
        'items': [
            {'name': 'terms.terms'},
            {'name': 'projects.projectplatformsettings'},
            {'name': 'members.memberplatformsettings'},
            {'name': 'cms.siteplatformsettings'},
            {'name': 'analytics.analyticsplatformsettings'},
            {'name': 'djmoney_rates.ratesource'},
            {'name': 'utils.language'},
            {'name': 'authtoken.token'},
        ]
    },

]

JET_SIDE_MENU_COMPACT = False
