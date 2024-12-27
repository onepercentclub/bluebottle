from django.utils.translation import gettext_lazy as _

JET_INDEX_DASHBOARD = "bluebottle.bluebottle_dashboard.dashboard.CustomIndexDashboard"
JET_APP_INDEX_DASHBOARD = (
    "bluebottle.bluebottle_dashboard.dashboard.CustomAppIndexDashboard"
)

JET_DEFAULT_THEME = "goodup"


JET_SIDE_MENU_ITEMS = [
    {
        "label": _("Initiatives"),
        "app_label": "initiatives",
        "permissions": ["initiatives.change_initiative"],
        "items": [
            {
                "name": "initiatives.initiative",
                "permissions": ["initiatives.change_initiative"],
            },
            {
                "name": "activities.activity",
                "permissions": ["activities.change_activity"],
            },
            {
                "name": "activities.contributor",
                "permissions": ["activities.change_contributor"],
            },
            {
                "name": "activities.contribution",
                "permissions": ["activities.change_contribution"],
            },
            {
                "name": "impact.impacttype",
                "permissions": ["impact.change_impacttype"],
                "enabled": "initiatives.InitiativePlatformSettings.enable_impact",
            },
            {
                "name": "categories.category",
                "permissions": ["categories.change_category"],
            },
            {"name": "initiatives.theme", "permissions": ["initiatives.change_theme"]},
            {
                "name": "organizations.organization",
                "permissions": ["organizations.change_organization"],
            },
            {"name": "geo.location", "permissions": ["geo.location"]},
        ],
    },
    {
        "label": _("Time Based"),
        "app_label": "time_based",
        "permissions": ["activities.change_activity"],
        "items": [
            {
                "name": "time_based.dateactivity",
                "permissions": ["time_based.change_dateactivity"],
            },
            {
                "name": "time_based.dateactivityslot",
                "permissions": ["time_based.change_dateactivityslot"],
            },
            {
                "name": "time_based.periodicactivity",
                "permissions": ["time_based.change_periodicactivity"],
            },
            {
                "name": "time_based.deadlineactivity",
                "permissions": ["time_based.change_deadlineactivity"],
            },
            {
                "name": "time_based.scheduleactivity",
                "permissions": ["time_based.change_scheduleactivity"],
            },
            {"name": "time_based.skill", "permissions": ["time_based.change_skill"]},
        ],
    },
    {
        "label": _("Collect"),
        "app_label": "collect",
        "permissions": ["activities.change_activity"],
        "enabled": "initiatives.InitiativePlatformSettings.collect_enabled",
        "items": [
            {
                "name": "collect.collectactivity",
            },
            {
                "name": "collect.collectcontributor",
            },
            {
                "name": "collect.collecttype",
            },
        ],
    },
    {
        "label": _("Deeds"),
        "app_label": "deeds",
        "permissions": ["activities.change_activity"],
        "enabled": "initiatives.InitiativePlatformSettings.deeds_enabled",
        "items": [
            {"name": "deeds.deed", "permissions": ["deeds.change_deed"]},
            {
                "name": "deeds.deedparticipant",
                "permissions": ["deeds.change_deedparticipant"],
            },
        ],
    },
    {
        "label": _("Funding"),
        "app_label": "funding",
        "permissions": ["funding.change_funding"],
        "items": [
            {"name": "funding.funding", "permissions": ["funding.change_funding"]},
            {"name": "funding.donor", "permissions": ["funding.change_donor"]},
            {"name": "funding.payment", "permissions": ["funding.change_payment"]},
            {
                "name": "funding.payoutaccount",
                "permissions": ["funding.change_payoutaccount"],
            },
            {
                "name": "funding.bankaccount",
                "permissions": ["funding.change_bankaccount"],
            },
            {"name": "funding.payout", "permissions": ["funding.change_payout"]},
        ],
    },
    {
        "label": _("Sharing"),
        "app_label": "sharing",
        "permissions": ["sharing.change_sharedactivity"],
        "items": [
            {"name": "sharing.sharedactivity", "permissions": ["sharing.change_sharedactivity"]},
            {"name": "sharing.platformconnection", "permissions": ["sharing.change_platformconnection"]},
        ],
    },
    {
        "label": _("Users"),
        "app_label": "members",
        "permissions": ["members.change_member"],
        "items": [
            {"name": "members.member", "permissions": ["members.change_member"]},
            {"name": "auth.group", "permissions": ["auth.change_group"]},
        ],
    },
    {
        "label": _("Segments"),
        "app_label": "segments",
        "permissions": ["segments.change_segmenttype"],
        "enabled": "members.MemberPlatformSettings.enable_segments",
        "items": [
            {
                "label": _("All segment types"),
                "name": "segments.segmenttype",
                "permissions": ["segments.change_segment"],
            },
        ],  # Segment type items are added programmatically in bluebottle_dashboard/utils.py
    },
    {
        "label": _("Offices"),
        "permissions": ["offices.change_officeregion"],
        "enabled": "initiatives.InitiativePlatformSettings.enable_office_regions",
        "items": [
            {"name": "geo.location", "permissions": ["geo.change_location"]},
            {
                "name": "offices.officesubregion",
                "permissions": ["offices.change_officesubregion"],
            },
            {
                "name": "offices.officeregion",
                "permissions": ["offices.change_officeregion"],
            },
        ],
    },
    {
        "label": _("Content"),
        "permissions": ["pages.change_page"],
        "items": [
            {"name": "pages.page", "permissions": ["pages.change_page"]},
            {
                "name": "news.newsitem",
                "label": _("News"),
                "permissions": ["news.change_newsitem"],
            },
            {
                "name": "cms.homepage",
                "label": _("Homepage"),
                "permissions": ["cms.change_homepage"],
            },
            {
                "name": "statistics.basestatistic",
                "label": _("Statistics"),
                "permissions": ["statistics.change_statistic"],
            },
            {"name": "slides.slide", "permissions": ["slides.change_slide"]},
            {
                "name": "cms.resultpage",
                "label": _("Result page"),
                "permissions": ["cms.change_resultpage"],
            },
            {
                "name": "cms.sitelinks",
                "label": _("Header & footer"),
                "permissions": ["cms.change_sitelinks"],
            },
            {
                "name": "notifications.messagetemplate",
                "label": _("Email templates"),
                "permissions": ["notifications.change_messagetemplate"],
            },
            {
                "name": "redirects.redirect",
                "permissions": ["redirects.change_redirect"],
            },
            {
                "name": "updates.update",
                "permissions": ["updates.change_update"],
            },
        ],
    },
    {
        "label": _("Reporting"),
        "app_label": "looker",
        "permissions": ["looker.access_looker_embeds"],
        "items": [],
    },
    {
        "label": _("Settings"),
        "permissions": ["terms.change_terms"],
        "items": [
            {"name": "terms.terms", "permissions": ["terms.change_terms"]},
            {
                "name": "cms.siteplatformsettings",
                "permissions": ["cms.change_siteplatformsettings"],
            },
            {
                "name": "members.memberplatformsettings",
                "permissions": ["members.change_memberplatformsettings"],
            },
            {
                "name": "notifications.notificationplatformsettings",
                "permissions": ["notifications.notificationplatformsettings"],
            },
            {
                "name": "mails.mailplatformsettings",
                "permissions": ["mails.change_mailplatformsettings"],
            },
            {
                "name": "initiatives.initiativeplatformsettings",
                "permissions": ["initiatives.change_initiativeplatformsettings"],
            },
            {
                "name": "funding.fundingplatformsettings",
                "permissions": ["funding.change_fundingplatformsettings"],
            },
            {
                "name": "funding.paymentprovider",
                "permissions": ["funding.change_paymentprovider"],
            },
            {
                "name": "analytics.analyticsplatformsettings",
                "permissions": ["analytics.change_analyticsplatformsettings"],
            },
            {
                "label": _("Manage Reporting"),
                "name": "looker.lookerembed",
            },
            {
                "name": "utils.translationplatformsettings",
                "permissions": ["utils.change_translationplatformsettings"],
            },
            {
                "name": "scim.scimplatformsettings",
                "permissions": ["scim.change_scimplatformsettings"],
            },
            {"name": "geo.country", "permissions": ["geo.change_country"]},
            {"name": "utils.language", "permissions": ["utils.change_language"]},
            {"name": "authtoken.token", "permissions": ["authtoken.change_token"]},
        ],
    },
]


JET_SIDE_MENU_COMPACT = False
