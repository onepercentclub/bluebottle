DROP VIEW IF EXISTS v_projects CASCADE;
CREATE OR REPLACE VIEW v_projects AS (
SELECT current_schema() as tenant,
	'project'::varchar as type,
	p.id as type_id,
	p.title as description,
	null::integer as parent_id,
	null::VARCHAR as parent_description,
	null::INTEGER as grand_parent_id,
	null::VARCHAR as grand_parent_description,
	p.campaign_ended AT TIME ZONE 'Europe/Amsterdam' as timestamp,
	pp.slug::varchar(20) as status,
	pl.start AT TIME ZONE 'Europe/Amsterdam' as event_timestamp,
	plp.slug::varchar(20) as event_status,
	p.owner_id as user_id,
	m.email as user_email,
	m.remote_id as user_remote_id,
	EXTRACT(YEAR FROM pl.start AT TIME ZONE 'Europe/Amsterdam') as year,
	EXTRACT(QUARTER FROM pl.start AT TIME ZONE 'Europe/Amsterdam') as quarter,
	EXTRACT(MONTH FROM pl.start AT TIME ZONE 'Europe/Amsterdam') as month,
	EXTRACT(WEEK FROM pl.start AT TIME ZONE 'Europe/Amsterdam') as week,
	l.name as location, lg.name as location_group,
	1 as value,
	NULL::INTEGER as pledged
FROM projects_project as p
LEFT JOIN projects_projectphaselog as pl
ON pl.project_id = p.id
LEFT JOIN members_member as m
ON m.id = p.owner_id
LEFT JOIN bb_projects_projectphase as plp
ON plp.id = pl.status_id
LEFT JOIN bb_projects_projectphase as pp
ON pp.id = p.status_id
LEFT JOIN geo_location as l
ON p.location_id = l.id
LEFT JOIN geo_locationgroup as lg
ON l.group_id = lg.id);


CREATE OR REPLACE VIEW v_tasks AS (
SELECT current_schema() as tenant,
       'task'::varchar as type,
	t.id as type_id,
	t.title as description,
	t.project_id as parent_id,
	p.description as parent_description,
	null::INTEGER as grand_parent_id,
	null::VARCHAR as grand_parent_description,
 	t.deadline AT TIME ZONE 'Europe/Amsterdam' as timestamp,
	t.status as status,
 	tl.start AT TIME ZONE 'Europe/Amsterdam' as event_timestamp,
	tl.status as event_status,
	author_id as user_id,
	m.email as user_email,
	m.remote_id as user_remote_id,
	EXTRACT(YEAR FROM t.deadline AT TIME ZONE 'Europe/Amsterdam') as year,
	EXTRACT(QUARTER FROM t.deadline AT TIME ZONE 'Europe/Amsterdam') as quarter,
	EXTRACT(MONTH FROM t.deadline AT TIME ZONE 'Europe/Amsterdam') as month,
	EXTRACT(WEEK FROM t.deadline AT TIME ZONE 'Europe/Amsterdam') as week,
	p.location as location,
	p.location_group as location_group,
	1 as value,
	t.time_needed::INTEGER as pledged
FROM tasks_task as t
LEFT JOIN tasks_taskstatuslog as tl
ON tl.task_id = t.id
LEFT JOIN v_projects as p
ON p.type_id = t.project_id
LEFT JOIN members_member as m
ON m.id = t.author_id);


CREATE OR REPLACE VIEW v_taskmembers AS (
SELECT current_schema() as tenant,
       'taskmember_hours'::varchar as type,
	tm.id as type_id,
	t.description as description,
	t.type_id as parent_id,
	t.description as parent_description,
	t.parent_id as grand_parent_id,
	t.parent_description as grand_parent_description,
	t.timestamp AT TIME ZONE 'Europe/Amsterdam' as timestamp,
	tm.status as status,
	tml.start AT TIME ZONE 'Europe/Amsterdam' as event_timestamp,
	tml.status as event_status,
	member_id as user_id,
	m.email as user_email,
	m.remote_id as user_remote_id,
	EXTRACT(YEAR FROM t.timestamp AT TIME ZONE 'Europe/Amsterdam') as year,
	EXTRACT(QUARTER FROM t.timestamp AT TIME ZONE 'Europe/Amsterdam') as quarter,
	EXTRACT(MONTH FROM t.timestamp AT TIME ZONE 'Europe/Amsterdam') as month,
	EXTRACT(WEEK FROM t.timestamp AT TIME ZONE 'Europe/Amsterdam') as week,
	t.location as location,
	t.location_group as location_group,
	tm.time_spent::integer as value,
	t.pledged as pledged
FROM tasks_taskmember as tm
LEFT JOIN tasks_taskmemberstatuslog as tml
ON tml.task_member_id = tm.id
LEFT JOIN (
	SELECT DISTINCT ON (1) v_tasks.type_id as task_type_id, *
	FROM v_tasks) as t
ON t.task_type_id = tm.task_id
LEFT JOIN members_member as m
ON m.id = tm.member_id);

-- Create report views on projects, tasks and task members
CREATE OR REPLACE VIEW v_project_successful_report AS (
SELECT DISTINCT on (1) type_id as filter_id, * FROM v_projects 
WHERE status = 'done-complete' AND event_status = 'done-complete'
ORDER BY filter_id, event_timestamp DESC);

-- For tasks we don't consider the event logs
CREATE OR REPLACE VIEW v_task_successful_report AS (
SELECT DISTINCT on (1) type_id as filter_id, * FROM v_tasks 
WHERE status = 'realized'
ORDER BY filter_id, timestamp DESC);

-- For task members we don't consider the event logs
CREATE OR REPLACE VIEW v_taskmember_successful_report AS (
SELECT DISTINCT on (1) type_id as filter_id, * FROM v_taskmembers 
WHERE status = 'realized' AND value > 0
ORDER BY filter_id, timestamp DESC);

-- Generate monthly 'success' report per project location
CREATE OR REPLACE VIEW v_month_report as (
SELECT * FROM (
SELECT year, quarter, month, location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, 'taskvolunteers'::varchar as type, count(user_id) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type) as m
ORDER BY m.year, m.quarter, m.month, m.location, m.type);

-- Generate quarterly 'success' report per project location
CREATE OR REPLACE VIEW v_quarter_report as (
SELECT * FROM (
SELECT year, quarter, 0::double precision as month, location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, 'taskvolunteers'::varchar as type, count(distinct(type_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type) as q
ORDER BY q.year, q.quarter, q.location, q.type);

-- Generate yearly 'success' report per project location
CREATE OR REPLACE VIEW v_year_report as (
SELECT * FROM (
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, 'taskvolunteers'::varchar as type, count(distinct(type_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type) as y
ORDER BY y.year, y.location, y.type);

-- Generate cumulative monthly 'success' report per project location
CREATE OR REPLACE VIEW v_month_cumulative_report as (
SELECT * FROM (
SELECT year, quarter, month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, location, type) as value
FROM v_project_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, location, type) as value
FROM v_task_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, quarter, month, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type
UNION
SELECT year, quarter, month, location, type, sum(sum(value)) OVER (ORDER BY year, quarter, month, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, location, type) as m
ORDER BY m.year, m.quarter, m.month, m.location, m.type);

-- Generate cumulative quarterly 'success' report per project location
CREATE OR REPLACE VIEW v_quarter_cumulative_report as (
SELECT * FROM (
SELECT year, quarter, 0::double precision as month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, location, type) as value
FROM v_project_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, location, type) as value
FROM v_task_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, quarter, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type
UNION
SELECT year, quarter, 0::double precision as month, location, type, sum(sum(value)) OVER (ORDER BY year, quarter, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, location, type) as m
ORDER BY m.year, m.quarter, m.location, m.type);

-- Generate cumulative yearly 'success' report per project location
CREATE OR REPLACE VIEW v_year_cumulative_report as (
SELECT * FROM (
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, location, type) as value
FROM v_project_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, sum(count(distinct type_id)) OVER (ORDER BY year, location, type) as value
FROM v_task_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, location, type, sum(sum(value)) OVER (ORDER BY year, location, type) as value
FROM v_taskmember_successful_report
GROUP BY year, location, type) as m
ORDER BY m.year, m.location, m.type);


-- Generate monthly 'success' report totals
CREATE OR REPLACE VIEW v_month_totals_report as (
SELECT * FROM (
SELECT year, quarter, month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, 'taskvolunteers'::varchar as type, count(distinct(type_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type) as m
ORDER BY m.year, m.quarter, m.month, m.type);

-- Generate quarterly 'success' report totals
CREATE OR REPLACE VIEW v_quarter_totals_report as (
SELECT * FROM (
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, 'taskvolunteers'::varchar as type, count(distinct(type_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type) as q
ORDER BY q.year, q.quarter, q.type);

-- Generate yearly 'success' report totals
CREATE OR REPLACE VIEW v_year_totals_report as (
SELECT * FROM (
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_project_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, count(distinct(type_id)) as value
FROM v_task_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, 'taskmembers'::varchar as type, count(distinct(user_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, 'taskvolunteers'::varchar as type, count(distinct(type_id)) as value
FROM v_taskmember_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, sum(value) as value
FROM v_taskmember_successful_report
GROUP BY year, type) as y
ORDER BY y.year, y.type);

-- Generate cumulative monthly  'success' report totals
CREATE OR REPLACE VIEW v_month_cumulative_totals_report as (
SELECT * FROM (
SELECT year, quarter, month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, type) as value
FROM v_project_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, type) as value
FROM v_task_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, quarter, month, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, month, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type
UNION
SELECT year, quarter, month, ''::varchar as location, type, sum(sum(value)) OVER (ORDER BY year, quarter, month, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, month, type) as m
ORDER BY m.year, m.quarter, m.month, m.type);

-- Generate cumulative quarterly 'success' report totals
CREATE OR REPLACE VIEW v_quarter_cumulative_totals_report as (
SELECT * FROM (
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, type) as value
FROM v_project_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, type) as value
FROM v_task_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, quarter, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, quarter, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type
UNION
SELECT year, quarter, 0::double precision as month, ''::varchar as location, type, sum(sum(value)) OVER (ORDER BY year, quarter, type) as value
FROM v_taskmember_successful_report
GROUP BY year, quarter, type) as m
ORDER BY m.year, m.quarter, m.type);

-- Generate cumulative quarterly 'success' report totals
CREATE OR REPLACE VIEW v_year_cumulative_totals_report as (
SELECT * FROM (
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, type) as value
FROM v_project_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, sum(count(distinct type_id)) OVER (ORDER BY year, type) as value
FROM v_task_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, 'taskmembers'::varchar as type, sum(count(distinct user_id)) OVER (ORDER BY year, type) as value
FROM v_taskmember_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, 'taskvolunteers'::varchar as type, sum(count(distinct type_id)) OVER (ORDER BY year, type) as value
FROM v_taskmember_successful_report
GROUP BY year, type
UNION
SELECT year, 0::double precision as quarter, 0::double precision as month, ''::varchar as location, type, sum(sum(value)) OVER (ORDER BY year, type) as value
FROM v_taskmember_successful_report
GROUP BY year, type) as m
ORDER BY m.year, m.type);
