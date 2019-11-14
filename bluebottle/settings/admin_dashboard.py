from django.utils.translation import ugettext_lazy as _


JET_INDEX_DASHBOARD = 'bluebottle.bluebottle_dashboard.dashboard.CustomIndexDashboard'
JET_APP_INDEX_DASHBOARD = 'bluebottle.bluebottle_dashboard.dashboard.CustomAppIndexDashboard'

JET_DEFAULT_THEME = 'goodup'


JET_SIDE_MENU_ITEMS = [  # A list of application or custom item dicts
    {
        'label': _('Initiatives'),
        'app_label': 'initiatives',
        'permissions': ['initiatives.change_initiative'],
        'items': [
            {
                'name': 'initiatives.initiative',
                'permissions': ['initiatives.change_initiative']
            },
            {
                'name': 'activities.activity',
                'permissions': ['activities.activity']
            },
            {
                'name': 'activities.contribution',
                'permissions': ['activities.activity']
            },
            {
                'name': 'categories.category',
                'permissions': ['categories.change_category']
            },
            {
                'name': 'bb_projects.projecttheme',
                'permissions': ['bb_projects.change_projecttheme']
            },
            {
                'name': 'organizations.organization',
                'permissions': ['organizations.change_organization']
            },
            {
                'name': 'geo.location',
                'permissions': ['geo.location']
            },
            {
                'name': 'bb_projects.projecttheme',
                'permissions': ['bb_projects.change_projecttheme']
            },
        ]
    },
    {
        'label': _('Events'),
        'app_label': 'events',
        'permissions': ['activities.change_activity'],
        'items': [
            {
                'name': 'events.event',
                'permissions': ['events.change_event']
            },
            {
                'name': 'events.participant',
                'permissions': ['events.change_participant']
            },
        ]
    },
    {
        'label': _('Tasks'),
        'app_label': 'assignments',
        'permissions': ['activities.change_activity'],
        'items': [
            {
                'name': 'assignments.assignment',
                'permissions': ['assignments.change_assignment']
            },
            {
                'name': 'assignments.applicant',
                'permissions': ['assignments.change_assignment']
            },
            {
                'name': 'tasks.skill',
                'permissions': ['tasks.change_skill']
            },
        ]
    },

    {
        'label': _('Funding'),
        'app_label': 'funding',
        'permissions': ['activities.change_activity'],
        'items': [
            {
                'name': 'funding.funding',
                'permissions': ['funding.change_funding']
            },
            {
                'name': 'funding.donation',
                'permissions': ['funding.change_donation']
            },
            {
                'name': 'funding.payment',
                'permissions': ['funding.change_payment']
            },
            {
                'name': 'funding.payoutaccount',
                'permissions': ['funding.change_payoutaccount']
            },
            {
                'name': 'funding.bankaccount',
                'permissions': ['funding.change_bankaccount']
            },
            {
                'name': 'funding.payout',
                'permissions': ['funding.change_payout']
            },
        ]
    },
    {
        'label': _('Legacy'),
        'app_label': 'projects',
        'permissions': ['projects.change_project'],
        'items': [
            {
                'name': 'projects.project',
                'permissions': ['projects.change_project']
            },
            {
                'name': 'categories.category',
                'permissions': ['categories.change_category']
            },
            {
                'name': 'fundraisers.fundraiser',
                'permissions': ['fundraisers.change_fundraiser']
            },
            {
                'name': 'bb_projects.projectphase',
                'permissions': ['bb_projects.change_projectphase']
            },
            {
                'name': 'bb_projects.projecttheme',
                'permissions': ['bb_projects.change_projecttheme']
            },
            {
                'name': 'organizations.organization',
                'permissions': ['organizations.organization']
            },
            {
                'name': 'geo.location',
                'permissions': ['geo.location']
            },
            {
                'name': 'votes.vote',
                'permissions': ['votes.vote']
            },
            {
                'name': 'tasks.task',
                'permissions': ['tasks.change_task']
            },
            {
                'name': 'tasks.taskmember',
                'permissions': ['tasks.change_task']
            },
            {
                'name': 'tasks.skill',
                'permissions': ['tasks.change_skill']
            },
            {
                'name': 'donations.donation',
                'permissions': ['donations.change_donation']
            },
            {
                'name': 'orders.order',
                'permissions': ['orders.change_order']
            },
            {
                'name': 'payouts.payoutaccount',
                'permissions': ['payouts_payoutaccount']
            },
            {
                'name': 'payments.orderpayment',
                'permissions': ['payments.change_orderpayment']
            },
            {
                'name': 'payments.payment',
                'permissions': ['payments.change_payment']
            },
            {
                'name': 'projects.projectplatformsettings',
                'permissions': ['projects.change_projectplatformsettings']
            },
        ]
    },
    {
        'label': _('Users'),
        'app_label': 'members',
        'permissions': ['members.change_member'],
        'items': [
            {
                'name': 'members.member',
                'permissions': ['members.change_member']
            },
            {
                'name': 'auth.group',
                'permissions': ['auth.change_group']
            },
        ]
    },
    {
        'label': _('Content'),
        'permissions': ['pages.change_page'],
        'items': [
            {
                'name': 'pages.page',
                'permissions': ['pages.change_page']
            },
            {
                'name': 'news.newsitem',
                'label': _('News'),
                'permissions': ['news.change_newsitem']
            },
            {
                'name': 'cms.homepage',
                'label': _('Homepage'),
                'permissions': ['cms.change_homepage']
            },
            {
                'name': 'slides.slide',
                'permissions': ['slides.change_slide']
            },
            {
                'name': 'cms.resultpage',
                'label': _('Result page'),
                'permissions': ['cms.change_resultpage']
            },
            {
                'name': 'cms.sitelinks',
                'label': _('Header & footer'),
                'permissions': ['cms.change_sitelinks']
            },
            {
                'name': 'redirects.redirect',
                'permissions': ['redirects.change_redirect']
            },
            {
                'name': 'wallposts.wallpost',
                'permissions': ['wallposts.change_wallpost']
            },
            {
                'url': 'wallposts.mediawallpost',
                'label': _('Media wall posts'),
                'permissions': ['wallposts.change_wallpost']
            },
            {
                'name': 'wallposts.reaction',
                'permissions': ['wallposts.change_wallpost']
            },
        ]
    },
    {
        'label': _('Reporting'),
        'app_label': 'looker',
        'permissions': ['looker.access_looker_embeds'],
        'items': []
    },
    {
        'label': _('Settings'),
        'permissions': ['terms.change_terms'],
        'items': [
            {
                'name': 'terms.terms',
                'permissions': ['terms.change_terms']
            },
            {
                'name': 'initiatives.initiativeplatformsettings',
                'permissions': ['initiatives.change_initiativeplatformsettings']
            },
            {
                'name': 'notifications.notificationplatformsettings',
                'permissions': ['notifications.notificationplatformsettings']
            },
            {
                'name': 'members.memberplatformsettings',
                'permissions': ['members.change_memberplatformsettings']
            },
            {
                'name': 'cms.siteplatformsettings',
                'permissions': ['cms.change_siteplatformsettings']
            },
            {
                'name': 'analytics.analyticsplatformsettings',
                'permissions': ['analytics.change_analyticsplatformsettings']
            },
            {
                'name': 'scim.scimplatformsettings',
                'permissions': ['scim.change_scimplatformsettings']
            },

            {
                'name': 'mails.mailplatformsettings',
                'permissions': ['mails.change_mailplatformsettings']
            },
            {
                'name': 'funding.paymentprovider',
                'permissions': ['funding.change_paymentprovider']
            },
            {
                'name': 'djmoney_rates.ratesource',
                'permissions': ['djmoney_rates.change_ratesource']
            },
            {
                'label': _('Manage Reporting'),
                'name': 'looker.lookerembed',
            },
            {
                'name': 'geo.country',
                'permissions': ['geo.change_country']
            },
            {
                'name': 'utils.language',
                'permissions': ['utils.change_language']
            },
            {
                'name': 'authtoken.token',
                'permissions': ['authtoken.change_token']
            },
        ]
    },

]

JET_SIDE_MENU_COMPACT = False
