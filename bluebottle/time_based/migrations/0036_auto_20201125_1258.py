# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-25 11:58
from __future__ import unicode_literals

from datetime import timedelta

from django.db import transaction
from django.db import migrations, transaction, connection


def insert(table, fields, values):
    with connection.cursor() as cursor:
        query = 'INSERT into {} ({})  VALUES ({})'.format(
            table,
            ", ".join('"{}"'.format(field) for field in fields),
            ','.join('%s' for field in fields)
        )
        actual_values = []

        for value in values:
            actual_values.append(
                [value[field] for field in fields ]
            )

        cursor.executemany(query, actual_values)


def migrate_activities(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Assignment = apps.get_model('assignments', 'Assignment')
    DateActivity = apps.get_model('time_based', 'DateActivity')
    PeriodActivity = apps.get_model('time_based', 'PeriodActivity')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    time_based_fields = (
        'activity_ptr_id', 'capacity', 'is_online', 'location_hint',
        'registration_deadline', 'location_id', 'review', 'expertise_id',
    )
    date_fields = (
        'timebasedactivity_ptr_id', 'start', 'duration', 'online_meeting_url',
    )
    period_fields = (
        'timebasedactivity_ptr_id', 'duration', 'duration_period', 'deadline' 
    )
        
    date_activities = []
    period_activities = []

    for event in Event.objects.values(
        'capacity', 'start', 'duration', 
        'is_online', 'location_id', 'location_hint',
        'online_meeting_url', 'registration_deadline',
        'activity_ptr_id'
        ):
        event['timebasedactivity_ptr_id'] = event['activity_ptr_id']
        event['review'] = False
        event['expertise_id'] = None
        if event['duration'] is not None:
            event['duration'] = timedelta(hours=event['duration'])

        date_activities.append(event)

    for assignment in Assignment.objects.values(
        'capacity', 'end_date_type', 'date', 'duration', 
        'is_online', 'location_id', 
        'online_meeting_url', 'registration_deadline',
        'activity_ptr_id', 'expertise_id'
        ):
        assignment['timebasedactivity_ptr_id'] = assignment['activity_ptr_id']
        assignment['review'] = True
        assignment['duration_period'] = 'overall'
        assignment['location_hint'] = ''
        assignment['online_meeting_url'] = ''

        if assignment['duration'] is not None: 
            assignment['duration'] = timedelta(hours=assignment['duration'])

        if assignment['end_date_type'] == 'on_date':
            assignment['start'] = assignment.pop('date')
            date_activities.append(assignment)
        else:
            if assignment['date']:
                assignment['deadline'] = assignment.pop('date').date()
            else:
                assignment['deadline'] = None

            period_activities.append(assignment)


    insert(
        'time_based_timebasedactivity', 
        time_based_fields,
        date_activities + period_activities
    )

    insert(
        'time_based_dateactivity', 
        date_fields,
        date_activities
    )
    insert(
        'time_based_periodactivity', 
        period_fields,
        period_activities
    )

    Event.objects.update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(DateActivity)
    )

    Assignment.objects.filter(end_date_type='on_date').update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(DateActivity)
    )

    Assignment.objects.exclude(end_date_type='on_date').update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(PeriodActivity)
    )


def migrate_contributors(apps, schema_editor):
    Participant = apps.get_model('events', 'Participant')
    Applicant = apps.get_model('assignments', 'Applicant')
    DateParticipant = apps.get_model('time_based', 'DateParticipant')
    PeriodParticipant = apps.get_model('time_based', 'PeriodParticipant')
    Contribution = apps.get_model('activities', 'Contribution')
    TimeContribution = apps.get_model('time_based', 'TimeContribution')

    ContentType = apps.get_model('contenttypes', 'ContentType')

    date_participant_fields = (
        'contributor_ptr_id', 
    )
    period_participant_fields = (
        'contributor_ptr_id', 'motivation', 'document_id'
    )
    contribution_fields = (
        'contributor_id', 'status', 'created', 'polymorphic_ctype_id'
    )
    time_contribution_fields = (
        'contribution_ptr_id', 'start', 'end', 'value'
    )

    date_participants = []
    period_participants = []
    time_contributions = []
    contributions = []
    time_contributions_ctype = ContentType.objects.get_for_model(TimeContribution).pk


    for participant in Participant.objects.values(
        'contributor_ptr_id', 'time_spent', 'activity__event__start', 'activity__event__duration',
        'status', 'created', 'contributor_date'
    ):
        duration = participant['activity__event__duration']
        date_participants.append({'contributor_ptr_id': participant['contributor_ptr_id']})

        if participant['status'] in ('accepted', 'active'):
            status = 'new'
        elif participant['status'] in ('withdrawn', 'failed', 'rejected', 'no_show'):
            status = 'failed'
        else:
            status = participant['status']

        contributions.append({
                'status': status,
                'contributor_id': participant['contributor_ptr_id'],
                'created': participant['created'],
                'polymorphic_ctype_id': time_contributions_ctype
        })
        time_contributions.append({
            'contributor_id': participant['contributor_ptr_id'],
            'start': participant['contributor_date'],
            'end': None,
            'value': timedelta(hours=participant['time_spent'] or 0) 
        })

    for applicant in Applicant.objects.values(
        'contributor_ptr_id', 'time_spent', 'motivation', 'document_id', 'activity__assignment__date', 
        'activity__assignment__end_date_type', 'created', 'status', 'contributor_date'
    ):
        participant = {
            'contributor_ptr_id': applicant['contributor_ptr_id'],
            'motivation': applicant['motivation'],
            'document_id': applicant['document_id'],
        }
        if applicant['activity__assignment__end_date_type'] == 'on_date':
            date_participants.append(participant)
        else:
            period_participants.append(participant)

        if applicant['status'] in ('accepted', 'active'):
            status = 'new'
        elif applicant['status'] in ('withdrawn', 'failed', 'rejected', 'no_show'):
            status = 'failed'
        else:
            status = applicant['status']

        contributions.append({
            'status': status,
            'contributor_id': applicant['contributor_ptr_id'],
            'created': applicant['created'],
            'polymorphic_ctype_id': time_contributions_ctype
        })
        time_contributions.append({
            'contributor_id': applicant['contributor_ptr_id'],
            'start': applicant['contributor_date'],
            'end': None,
            'value': timedelta(hours=applicant['time_spent'] or 0)
        })

    insert('time_based_dateparticipant', date_participant_fields, date_participants)
    insert('time_based_periodparticipant', period_participant_fields, period_participants)
    insert('activities_contribution', contribution_fields, contributions)

    contributions = dict(Contribution.objects.values_list('contributor_id', 'id'))
    for time_contribution in time_contributions:
        time_contribution['contribution_ptr_id'] = contributions[time_contribution['contributor_id']]

    insert('time_based_timecontribution', time_contribution_fields, time_contributions)

    Participant.objects.update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(DateParticipant)
    )

    Applicant.objects.filter(activity__assignment__end_date_type='on_date').update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(DateParticipant)
    )

    Applicant.objects.exclude(activity__assignment__end_date_type='on_date').update(
        polymorphic_ctype_id=ContentType.objects.get_for_model(PeriodParticipant)
    )

    DateParticipant.objects.filter(
        status__in=('succeeded', 'active', )
    ).update(
        status='accepted'
    )

    PeriodParticipant.objects.filter(
        status__in=('succeeded', 'active', )
    ).update(
        status='accepted'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0035_auto_20201120_1318'),
        ('assignments', '0024_auto_20201112_1519'),
        ('events', '0020_auto_20201112_1519')
    ]

    operations = [
        migrations.RunPython(migrate_activities, migrations.RunPython.noop), 
        migrations.RunPython(migrate_contributors, migrations.RunPython.noop), 
    ]
