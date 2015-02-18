from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.db import models
from django.core.management import call_command


def get_task_skill_model():
    return get_model_class('TASKS_SKILL_MODEL')


def get_task_model():
    return get_model_class('TASKS_TASK_MODEL')


def get_taskmember_model():
    return get_model_class('TASKS_TASKMEMBER_MODEL')


def get_taskfile_model():
    return get_model_class('TASKS_TASKFILE_MODEL')


def get_project_model():
    return get_model_class('PROJECTS_PROJECT_MODEL')


def get_project_phaselog_model():
    return get_model_class('PROJECTS_PHASELOG_MODEL')


def get_donation_model():
    return get_model_class('DONATIONS_DONATION_MODEL')


def get_order_model():
    return get_model_class('ORDERS_ORDER_MODEL')


def get_fundraiser_model():
    return get_model_class('FUNDRAISERS_FUNDRAISER_MODEL')


def get_organization_model():
    return get_model_class('ORGANIZATIONS_ORGANIZATION_MODEL')


def get_organizationmember_model():
    return get_model_class('ORGANIZATIONS_MEMBER_MODEL')


def get_organizationdocument_model():
    return get_model_class('ORGANIZATIONS_DOCUMENT_MODEL')


def get_payment_logger_model():
    return get_model_class('PAYMENT_LOGGER_MODEL')


def get_project_payout_model():
    return get_model_class('PAYOUTS_PROJECTPAYOUT_MODEL')


def get_organization_payout_model():
    return get_model_class('PAYOUTS_ORGANIZATIONPAYOUT_MODEL')


def get_client_model():
    return get_model_class('TENANT_MODEL')


def get_auth_user_model():
    return get_user_model()


def get_model_class(model_name=None):
    """
    Returns a model class
    model_name: The model eg 'User' or 'Project'
    """

    #remove this
    if model_name == 'AUTH_USER_MODEL':
        model = get_user_model()

    else:
        model_path = getattr(settings, model_name)
        try:
            app_label, model_class_name = model_path.split('.')
        except ValueError:
            raise ImproperlyConfigured(
                "{0} must be of the form 'app_label.model_name'").format(model_name)

        model = get_model(app_label, model_class_name)
        if model is None:
            raise ImproperlyConfigured(
                "{0} refers to model '{1}' that has not been "
                "installed".format(model_name, model_path))

    return model


def _map_model(name, model_name):
    """
    Derive some partials of a model based on settings
    """
    model = getattr(settings, model_name)
    db_table = getattr(get_model_class(model_name).Meta, 'db_table', model.lower().replace('.', '_'))
    return {
        name: {
            'model': model,
            'model_lower': model.lower(),
            'class': model.split('.')[1],
            'app': model.split('.')[0],
            'table': db_table
        }
    }


def get_model_mapping():
    """
    Return a dictionary with all base models and their parts (model, class, app, table).

    This is used by bb_schemamigration command.
    https://github.com/onepercentclub/bluebottle/wiki/Migrations
    """
    map = dict(_map_model('user', 'AUTH_USER_MODEL').items()

        + _map_model('project', 'PROJECTS_PROJECT_MODEL').items()
        + _map_model('project_phaselog', 'PROJECTS_PHASELOG_MODEL').items()

        + _map_model('task', 'TASKS_TASK_MODEL').items()
        + _map_model('task_skill', 'TASKS_SKILL_MODEL').items()
        + _map_model('task_member', 'TASKS_TASKMEMBER_MODEL').items()
        + _map_model('task_file', 'TASKS_TASKFILE_MODEL').items()

        + _map_model('order', 'ORDERS_ORDER_MODEL').items()
        + _map_model('donation', 'DONATIONS_DONATION_MODEL').items()
        + _map_model('project_payout', 'PAYOUTS_PROJECTPAYOUT_MODEL').items()
        + _map_model('organization_payout', 'PAYOUTS_ORGANIZATIONPAYOUT_MODEL').items()
        + _map_model('fundraiser', 'FUNDRAISERS_FUNDRAISER_MODEL').items()
        + _map_model('organization', 'ORGANIZATIONS_ORGANIZATION_MODEL').items()
        + _map_model('organization_member', 'ORGANIZATIONS_MEMBER_MODEL').items()
        + _map_model('organization_document', 'ORGANIZATIONS_DOCUMENT_MODEL').items()
        + _map_model('client', 'TENANT_MODEL').items()
    )
    return map


def load_fixture(file_name, orm):
    original_get_model = models.get_model

    def get_model_southern_style(*args):
        try:
            return orm['.'.join(args)]
        except:
            return original_get_model(*args)

    models.get_model = get_model_southern_style

    call_command('loaddata', file_name)

    models.get_model = original_get_model

