from django.db import models
from django.utils.translation import ugettext as _
from django_pgviews import view as pg


class BaseRawReport(models.Model):
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

    class Meta:
        abstract = True


class ProjectDoneManager(models.Manager):
    def get_queryset(self):
        return super(ProjectDoneManager, self).get_queryset(). \
            filter(status='done-complete', event_status='done-complete')


class ProjectRawReport(BaseRawReport, pg.View):
    projection = ['analytics.BaseRawReport.*', ]
    done_objects = ProjectDoneManager()

    sql = """
        SELECT "current_schema"() AS tenant,
            'project'::character varying AS type,
            p.id AS type_id,
            NULL::integer AS parent_id,
            p.campaign_ended AS "timestamp",
            pp.slug::character varying(20) AS status,
            pl.start AS event_timestamp,
            plp.slug::character varying(20) AS event_status,
            p.owner_id AS user_id,
            date_part('year'::text, pl.start) AS year,
            date_part('quarter'::text, pl.start) AS quarter,
            date_part('month'::text, pl.start) AS month,
            date_part('week'::text, pl.start) AS week,
            l.name AS location,
            lg.name AS location_group,
            1 AS value
            FROM projects_project p
            LEFT JOIN (
                SELECT max(start) AS start, project_id, status_id
                FROM projects_projectphaselog
                GROUP BY project_id, status_id
            ) pl ON pl.project_id = p.id
            LEFT JOIN bb_projects_projectphase plp ON plp.id = pl.status_id
            LEFT JOIN bb_projects_projectphase pp ON pp.id = p.status_id
            LEFT JOIN geo_location l ON p.location_id = l.id
            LEFT JOIN geo_locationgroup lg ON l.group_id = lg.id;
           """

    class Meta:
        app_label = 'analytics'
        db_table = 'v_projects'
        managed = False


class TaskRawReport(BaseRawReport, pg.View):
    projection = ['analytics.BaseRawReport.*', ]
    sql = """
        SELECT current_schema() as tenant,
            'task'::varchar as type,
            t.id as type_id,
            t.project_id as parent_id,
            t.deadline as timestamp,
            t.status as status,
            tl.start as event_timestamp,
            tl.status as event_status,
            author_id as user_id,
            EXTRACT(YEAR FROM t.deadline) as year,
            EXTRACT(QUARTER FROM t.deadline) as quarter,
            EXTRACT(MONTH FROM t.deadline) as month,
            EXTRACT(WEEK FROM t.deadline) as week,
            l.name as location,
            lg.name as location_group,
            1 as value
        FROM tasks_task as t
        LEFT JOIN tasks_taskstatuslog as tl
        ON tl.task_id = t.id
        LEFT JOIN projects_project as p
        ON p.id = t.project_id
        LEFT JOIN geo_location as l
        ON p.location_id = l.id
        LEFT JOIN geo_locationgroup as lg
        ON l.group_id = lg.id
    """

    class Meta:
        app_label = 'analytics'
        db_table = 'v_tasks'
        managed = False


class TaskMemberRawReport(BaseRawReport, pg.View):
    projection = ['analytics.BaseRawReport.*', ]
    sql = """
        SELECT current_schema() as tenant,
               'taskmember_hours'::varchar as type,
            tm.id as type_id,
            t.type_id as parent_id,
            t.timestamp as timestamp,
            tm.status as status,
            tml.start as event_timestamp,
            tml.status as event_status,
            member_id as user_id,
            EXTRACT(YEAR FROM t.timestamp) as year,
            EXTRACT(QUARTER FROM t.timestamp) as quarter,
            EXTRACT(MONTH FROM t.timestamp) as month,
            EXTRACT(WEEK FROM t.timestamp) as week,
            l.name as location,
            lg.name as location_group,
            tm.time_spent::integer as value
        FROM tasks_taskmember as tm
        LEFT JOIN tasks_taskmemberstatuslog as tml
        ON tml.task_member_id = tm.id
        LEFT JOIN (
            SELECT DISTINCT ON (1) v_tasks.type_id as task_type_id, *
            FROM v_tasks) as t
        ON t.task_type_id = tm.task_id
        LEFT JOIN projects_project as p
        ON p.id = t.parent_id
        LEFT JOIN geo_location as l
        ON p.location_id = l.id
        LEFT JOIN geo_locationgroup as lg
        ON l.group_id = lg.id)
    """

    class Meta:
        app_label = 'analytics'
        db_table = 'v_taskmembers'
        managed = False
