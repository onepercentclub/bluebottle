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
        'label': _('Tasks'),
        'app_label': 'tasks',
        'permissions': ['tasks.change_task'],
        'items': [
            {'name': 'tasks.task'},
            {'name': 'tasks.taskmember'},
            {'name': 'tasks.skill'},
        ]
    },
    {
        'label': 'Members',
        'app_label': 'members',
        'permissions': ['members.change_member'],
        'items': [
            {'name': 'members.member'},
            {'name': 'auth.group'},
        ]
    },
    {
        'label': 'Wallposts',
        'permissions': ['wallposts.wallpost'],
        'items': [
            {'name': 'wallposts.wallpost'},
            {'name': 'wallposts.systemwallpost'},
            {'name': 'wallposts.mediawallpost'},
            {'name': 'wallposts.textwallpost'},
            {'name': 'wallposts.reaction'},
        ]
    },
    {
        'label': _('Site Content'),
        'items': [
            {'name': 'cms.resultpage'},
            {'name': 'cms.homepage'},
            {'name': 'cms.sitelinks'},
            {'name': 'pages.page'},

            {'name': 'slides.slide'},
            {'name': 'redirects.redirect'},
            {'name': 'news.newsitem'},
            {'name': 'terms.terms'},
            {'name': 'contact.contactmessage'},

        ]
    },
    {
        'label': _('Donations'), 'items': [
            {'name': 'donations.donation'},
            {'name': 'orders.order'},
            {'name': 'recurring_donations.monthlybatch'},
            {'name': 'recurring_donations.monthlydonation'},
            {'name': 'recurring_donations.monthlydonor'},
            {'name': 'recurring_donations.monthlyorder'},
        ]
    },
    {
        'label': _('Finance'),
        'items': [
            {'name': 'payments.orderpayment'},
            {'name': 'payments.payment'},
            {'name': 'djmoney_rates.ratesource'},
        ]
    },
    {
        'label': _('Platform settings'),
        'items': [
            {'name': 'projects.projectplatformsettings'},
            {'name': 'members.memberplatformsettings'},
            {'name': 'cms.siteplatformsettings'},
            {'name': 'analytics.analyticsplatformsettings'},
            {'name': 'utils.language'},
            {'name': 'authtoken.token'},

        ]
    },

]

JET_SIDE_MENU_COMPACT = False
