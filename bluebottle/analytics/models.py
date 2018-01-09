from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


# get_report_model returns a Django model for accessing the report views
def get_report_model(db_table):
    """Get Django model for accessing the views for reporting

    Args:
        db_table: The view name as created in the DB.

    Returns:
        A Django model

    """

    class ReportMetaClass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            model = super(ReportMetaClass, cls).__new__(cls, name, bases, attrs)
            model._meta.db_table = db_table
            model._meta.managed = False
            return model

    class ReportClass(models.Model):
        __metaclass__ = ReportMetaClass

        #  Column  |           Type         |
        # ---------+------------------------+
        # year     | double precision       |
        # quarter  | double precision       |
        # month    | double precision       |
        # location | character varying(255) |
        # type     | character varying      |
        # value    | bigint                 |

        year = models.PositiveSmallIntegerField(_('year'))
        quarter = models.PositiveSmallIntegerField(_('quarter'))
        month = models.PositiveSmallIntegerField(_('month'), primary_key=True)
        location = models.CharField(_('location'), max_length=255)
        type = models.CharField(_('type'), max_length=20)
        value = models.IntegerField(_('value'))

    return ReportClass


def get_raw_report_model(db_table):
    """Get Django model for accessing the raw views used in reporting

    Args:
        db_table: The view name as created in the DB.

    Returns:
        A Django model

    """

    class RawReportMetaClass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            model = super(RawReportMetaClass, cls).__new__(cls, name, bases, attrs)
            model._meta.db_table = db_table
            model._meta.managed = False
            return model

    class RawReportClass(models.Model):
        __metaclass__ = RawReportMetaClass

        #          Column          |            Type             |
        # -------------------------+-----------------------------+
        # tenant                   | name                        |
        # type                     | character varying           |
        # type_id                  | integer                     |
        # description              | character varying(255)      |
        # parent_id                | integer                     |
        # parent_description       | character varying           |
        # grand_parent_id          | integer                     |
        # grand_parent_description | character varying           |
        # timestamp                | timestamp without time zone |
        # status                   | character varying(20)       |
        # status_friendly          | character varying(80)       |
        # event_timestamp          | timestamp without time zone |
        # event_status             | character varying(20)       |
        # user_id                  | integer                     |
        # user_email               | character varying(254)      |
        # user_remote_id           | character varying(75)       |
        # year                     | double precision            |
        # quarter                  | double precision            |
        # month                    | double precision            |
        # week                     | double precision            |
        # location                 | character varying(255)      |
        # location_group           | character varying(255)      |
        # value                    | integer                     |
        # value_alt                | integer                     |

        tenant = models.CharField(_('tenant'), max_length=255, primary_key=True)
        type = models.CharField(_('type'), max_length=255)
        type_id = models.PositiveIntegerField(_('type_id'))
        description = models.CharField(_('description'), max_length=255)
        parent_id = models.PositiveIntegerField(_('parent_id'))
        parent_description = models.CharField(_('parent_description'), max_length=255)
        grand_parent_id = models.PositiveIntegerField(_('grand_parent_id'))
        grand_parent_description = models.CharField(_('grand_parent_description'), max_length=255)
        timestamp = models.DateTimeField(_('timestamp'))
        status = models.CharField(_('status'), max_length=20)
        status_friendly = models.CharField(_('status_friendly'), max_length=80)
        event_timestamp = models.DateTimeField(_('event_timestamp'))
        event_status = models.CharField(_('event_status'), max_length=20)
        user_id = models.PositiveIntegerField(_('user_id'))
        user_email = models.CharField(_('user_email'), max_length=255)
        user_remote_id = models.PositiveIntegerField(_('user_remote_id'))
        year = models.PositiveSmallIntegerField(_('year'))
        quarter = models.PositiveSmallIntegerField(_('quarter'))
        month = models.PositiveSmallIntegerField(_('month'))
        week = models.PositiveSmallIntegerField(_('week'))
        location = models.CharField(_('location'), max_length=255)
        location_group = models.CharField(_('location_group'), max_length=255)
        value = models.IntegerField(_('value'))
        value_alt = models.IntegerField(_('value'))

    return RawReportClass


class AnalyticsAdapter(models.Model):
    type = models.CharField(max_length=100, default='GoogleAnalytics')
    code = models.CharField(max_length=100, null=True, blank=True)
    analytics_settings = models.ForeignKey('analytics.AnalyticsPlatformSettings', related_name='adapters')


class AnalyticsPlatformSettings(BasePlatformSettings):

    class Meta:
        verbose_name_plural = _('analytics platform settings')
        verbose_name = _('analytics platform settings')
