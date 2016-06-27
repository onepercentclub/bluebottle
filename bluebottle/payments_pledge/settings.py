# This file is only added so the Pledge translation is detected. It's not
# meant for actual usage. Technically nothing but the 'name' key is needed
# but the rest is left for clarity purposes
_ = lambda s: s

PLEDGE_METHOD = {
    'provider': 'pledge',
    'id': 'pledge-standard',
    'name': _('Pledge'),
    'profile': 'standard',
    'method_access_handler': 'bluebottle.payments.tests.test_services.method_access_handler'
}