RECURRING_DONATIONS_ENABLED = {{ recurring_donations }}

CONTACT_EMAIL = '{{ contact_email }}'

TENANT_JWT_SECRET = '{{ jwt_secret}}'

DEFAULT_COUNTRY_CODE = '{{ country_code }}'

gettext_noop = lambda s: s

LANGUAGES = (
    {% if languages.nl %}('nl', gettext_noop('Dutch')),{% endif %}
    {% if languages.en %}('en', gettext_noop('English')),{% endif %}

)

LANGUAGE_CODE = '{{ language_code }}'

{% if project_type == 'both' %}
PROJECT_CREATE_TYPES = ['funding', 'sourcing']
PROJECT_CREATE_FLOW = 'choice'

{% else %}
PROJECT_CREATE_TYPES = ['{{ project_type }}',]
{% endif %}

MIXPANEL = '{{ mixpanel }}'
MAPS_API_KEY = '{{ maps }}'

PROJECT_PAYOUT_FEES = {
    'beneath_threshold': 1,
    'fully_funded': .05,
    'not_fully_funded': .05
}

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'supports_recurring': False,
    },
)

TENANT_MAIL_PROPERTIES = {
    'logo': '/static/assets/frontend/{{ client_name}}/images/logo-email.gif',
    'address': '{{ mail_address }}', 
    'sender': '{{ mail_sender }}', 
    'footer': '{{ mail_footer }}',
    'website': '{{ mail_website }}',
}

DATE_FORMAT = '{{ date_format }}'
