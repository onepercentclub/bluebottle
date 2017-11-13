from django.db import models
from django.utils.translation import ugettext as _


def get_report_model(db_table):
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
    class RawReportMetaClass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            model = super(RawReportMetaClass, cls).__new__(cls, name, bases, attrs)
            model._meta.db_table = db_table
            model._meta.managed = False
            return model

    class RawReportClass(models.Model):
        __metaclass__ = RawReportMetaClass

        #     Column      |           Type           |
        # ----------------+--------------------------+
        # tenant          | name                     |
        # type            | character varying        |
        # type_id         | integer                  |
        # parent_id       | integer                  |
        # timestamp       | timestamp with time zone |
        # status          | character varying(20)    |
        # event_timestamp | timestamp with time zone |
        # event_status    | character varying(20)    |
        # user_id         | integer                  |
        # year            | double precision         |
        # quarter         | double precision         |
        # month           | double precision         |
        # week            | double precision         |
        # location        | character varying(255)   |
        # location_group  | character varying(255)   |
        # value           | integer                  |
        tenant = models.CharField(_('tenant'), max_length=255, primary_key=True)
        type = models.CharField(_('type'), max_length=255)
        type_id = models.PositiveIntegerField(_('type_id'))
        parent_id = models.PositiveIntegerField(_('parent_id'))
        timestamp = models.DateTimeField(_('timestamp'))
        status = models.CharField(_('status'), max_length=20)
        event_timestamp = models.DateTimeField(_('event_timestamp'))
        event_status = models.CharField(_('event_status'), max_length=20)
        user_id = models.PositiveIntegerField(_('user_id'))
        year = models.PositiveSmallIntegerField(_('year'))
        quarter = models.PositiveSmallIntegerField(_('quarter'))
        month = models.PositiveSmallIntegerField(_('month'))
        week = models.PositiveSmallIntegerField(_('week'))
        location = models.CharField(_('location'), max_length=255)
        location_group = models.CharField(_('location_group'), max_length=255)
        value = models.IntegerField(_('value'))

    return RawReportClass


def export_report(table_name):
    ReportModel = get_report_model(table_name)
    results = ReportModel.objects.all()
    for row in results:
        print(int(row.year), int(row.quarter), int(row.month), row.location, row.type, int(row.value))


def export_raw_report(table_name):
    RawReportModel = get_raw_report_model(table_name)
    results = RawReportModel.objects.all()
    for row in results:
        print(row.type, int(row.type_id), int(row.parent_id or 0),
              row.timestamp, row.status, row.location, row.type, int(row.value))
