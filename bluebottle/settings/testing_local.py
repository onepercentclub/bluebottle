from bluebottle.settings.testing import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'bluebottle.clients.postgresql_backend',
        'HOST': 'postgres',
        'PORT': '5432',
        'NAME': 'reef',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'DISABLE_SERVER_SIDE_CURSORS': True # this prevents issues with connection pooling
    },

}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'elasticsearch:9200'
    },

}

SLOW_TEST_THRESHOLD_MS = 1000
ELASTICSEARCH_DSL_AUTOSYNC = False

CELERY_MAIL = False

CONFLUENCE = {
    "tenant": "goodup_demo",
    "api": {"domain": "", "user": "", "key": ""},
    "prod_models": [
        {
            "title": "States - Initiative",
            "model": "bluebottle.initiatives.models.Initiative",
            "page_id": "",
        },
    ],
    "dev_models": [
        # Time-based Activities
        {
            "title": "[DEV] States - Time based - Activity on a date",
            "model": "bluebottle.time_based.models.DateActivity",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Participant on a date",
            "model": "bluebottle.time_based.models.DateParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Activity slot",
            "model": "bluebottle.time_based.models.DateActivitySlot",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Slot participant",
            "model": "bluebottle.time_based.models.SlotParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Deadline Activity",
            "model": "bluebottle.time_based.models.DeadlineActivity",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Periodic Activity",
            "model": "bluebottle.time_based.models.PeriodicActivity",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Schedule Activity",
            "model": "bluebottle.time_based.models.ScheduleActivity",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Deadline Participant",
            "model": "bluebottle.time_based.models.DeadlineParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Periodic Participant",
            "model": "bluebottle.time_based.models.PeriodicParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Schedule Participant",
            "model": "bluebottle.time_based.models.ScheduleParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Team Schedule Participant",
            "model": "bluebottle.time_based.models.TeamScheduleParticipant",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Schedule Slot",
            "model": "bluebottle.time_based.models.ScheduleSlot",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Team Schedule Slot",
            "model": "bluebottle.time_based.models.TeamScheduleSlot",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Team",
            "model": "bluebottle.time_based.models.Team",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Team Member",
            "model": "bluebottle.time_based.models.TeamMember",
            "page_id": "",
        },
        {
            "title": "[DEV] States - Time based - Time contribution",
            "model": "bluebottle.time_based.models.TimeContribution",
            "page_id": "",
        },
    ],
}
