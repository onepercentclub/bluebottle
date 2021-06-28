import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
from random import random
from urllib.parse import unquote

import pytz
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.db import connection
from django.db import models
from django.utils.timezone import now

from bluebottle.activities.models import Activity, Contributor, Organizer, EffortContribution, Contribution
from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.files.models import Image
from bluebottle.geo.models import Geolocation, Country, Place
from bluebottle.initiatives.models import Theme, Initiative
from bluebottle.members.models import Member
from bluebottle.organizations.models import OrganizationContact, Organization
from bluebottle.segments.models import SegmentType, Segment
from bluebottle.time_based.models import DateActivity, DateActivitySlot, SlotParticipant, DateParticipant, \
    TimeBasedActivity, TimeContribution

ams = pytz.timezone('Europe/Amsterdam')
nld_id = 149


def create_model(Model, app_label='children', module='', options=None):
    """
    Create specified model
    """
    model_name = Model.__name__

    class Meta:
        managed = False
        db_table = Model._meta.db_table

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    fields = dict()
    for field in Model._meta.fields:
        name = field.attname
        if name == 'id' or field.attname == 'id':
            continue
        if name.endswith('ptr_id'):
            fields[name] = models.IntegerField(primary_key=True)
            continue
        if name.endswith('_id'):
            name = name.replace('_id', '')
        if field.model.__name__ == model_name:
            fields[name] = field.clone()

    # Hack it away
    if model_name == 'DateActivity':
        del fields['activity_ptr_id']

    # Create the class, which automatically triggers ModelBase processing
    attrs.update(fields)
    model = type(f'{model_name}Shadow', (models.Model,), attrs)
    return model


def add_tz(date):
    if not date:
        return date
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    if date.tzinfo:
        return date
    return ams.localize(date)


status_mapping = {
    'In Progress': 'open',
    'Planned': 'draft',
    'completed': 'succeeded',
    'confirmed': 'succeeded',
    'no-show': 'cancelled',
}

mapping = {
    'initiative': {
        'id': 'id',
        'title': 'name_nl',
        'slug': 'slug_nl',
        'created': 'created_at',
    },
    'activity': {
        'initiative_id': 'id',
        'title': 'name_nl',
        'slug': 'slug_nl',
        'created': 'created_at',
    },
    'time_based_activity': {
        'activity_ptr_id': 'id',
    },
    'date_activity': {
        'timebasedactivity_ptr_id': 'id',
    },
    'slot': {
        'id': 'id',
        'activity_id': 'activity_id',
        'start': 'start_time',
        'created': 'created_at',
        'capacity': 'desired_number_of_volunteers'
    },
    'user': {
        'id': 'id',
        'first_name': 'firstname',
        'last_name': 'lastname',
        'email': 'email',
        'created': 'created_at',
        'password': 'password',
        'phone_number': 'phone',
        'birthdate': 'birthday',
    },
    'location': {
        'id': 'id',
        'locality': 'city',
        'street': 'street',
        'postal_code': 'zipcode',
        'created': 'created_at',
    },
    'segment': {
        'id': 'id',
        'name': 'name',
        'slug': 'slug',
    }
}


def split_description(text):
    if not text:
        return {}
    html = unescape(text)
    parts = {}
    bs = BeautifulSoup(html, 'lxml')
    for h3 in bs.find_all('h3'):
        title = h3.text
        if 'impact' in title or 'Impact' in title:
            title = 'impact'
        if 'activiteit' in title or 'Activiteit' in title:
            title = 'intro'
        content = ''
        sibling = h3.next_sibling
        while sibling and sibling.name == 'p':
            content += sibling.text
            sibling = sibling.next_sibling
        if title and content:
            parts[h3.text] = content
    return parts


def extract_pitch(text):
    parts = split_description(text)
    if 'impact' in parts:
        return parts['impact']
    if 'intro' in parts:
        return parts['intro']
    return '-'


def extract_story(text):
    if not text:
        return '-'
    html = unescape(text)
    bs = BeautifulSoup(html, 'lxml')
    h3 = bs.find('h3')
    if h3:
        h3.extract()
    return bs.html


def update_sequence(table):
    with connection.cursor() as cursor:
        sql = "SELECT setval(pg_get_serial_sequence('{0}','id'), " \
              "coalesce(max(id), 1), max(id) IS NOT null) FROM \"{0}\";".format(table)
        cursor.execute(sql)


def import_themes(rows):
    for row in rows:
        theme = Theme()
        theme.id = row.find("field[@name='id']").text
        theme.slug = row.find("field[@name='slug']").text
        theme.save()
        theme.set_current_language('nl')
        theme.name = row.find("field[@name='name']").text
        theme.set_current_language('en')
        theme.name = row.find("field[@name='name']").text
        theme.save()
    update_sequence('initiatives_theme')


def import_initiatives(rows):
    TimeBasedActivityShadow = create_model(TimeBasedActivity)
    DateActivityShadow = create_model(DateActivity)
    OrganizerShadow = create_model(Organizer)
    EffortContributionShadow = create_model(EffortContribution)
    date_type = ContentType.objects.get_for_model(DateActivity).id
    organizer_type = ContentType.objects.get_for_model(Organizer).id
    effort_type = ContentType.objects.get_for_model(EffortContribution).id

    initiatives = []
    activities = []
    time_based_activities = []
    date_activities = []
    contacts = []
    images = []
    cities = []
    contributors = []
    organizers = []
    contributions = []
    effort_contributions = []
    cares_user = Member.objects.get(email='info@nlcares.nl')
    for row in rows:
        initiative_id = row.find("field[@name='id']").text

        # status = row.find("field[@name='status']").text
        # status = status_mapping[status]
        initiative = Initiative(
            id=initiative_id,
            status='approved',
            has_organization=False,
        )

        # Extract contact
        email = row.find("field[@name='contact_email']").text or 'initiator{}@example.com'.format(initiative_id)
        first_name = row.find("field[@name='contact_firstname']").text or 'Nomen'
        last_name = row.find("field[@name='contact_lastname']").text or 'Nescio'
        contact_phone = row.find("field[@name='contact_phone']").text or ''
        contact = OrganizationContact(
            name="{} {}".format(first_name, last_name),
            email=email,
            phone=contact_phone,
            owner=cares_user
        )
        contacts.append(contact)

        try:
            owner = Member.objects.get(email=email)
        except Member.DoesNotExist:
            owner = cares_user
        description = row.find("field[@name='description_nl']").text or '-'
        # story = extract_story(description)
        story = description
        for k in mapping['initiative']:
            v = mapping['initiative'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            initiative.__setattr__(k, value)
        initiative.owner = owner
        initiative.organization_contact = contact
        initiative.pitch = extract_pitch(description)
        initiative.story = story

        image_url = row.find("field[@name='image_url']").text
        if image_url:
            try:
                image = Image(
                    owner=owner
                )
                image_url = image_url.replace('https://s3.eu-central-1.amazonaws.com', 'data')
                image_url = unquote(image_url)
                image.file.save(
                    "image_{}-{}.jpg".format(initiative_id, int(1000 * random())),
                    File(open(image_url, 'rb'))
                )
                images.append(image)
                initiative.image = image
            except FileNotFoundError:
                pass
        initiative.created = add_tz(initiative.created)
        initiatives.append(initiative)

        activity = Activity(
            id=initiative_id,
        )
        for k in mapping['activity']:
            v = mapping['activity'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            activity.__setattr__(k, value)
            activity.polymorphic_ctype_id = date_type
            activity.description = story
            activity.status = 'open'
            activity.created = add_tz(activity.created)
            activity.owner = owner
        activities.append(activity)

        time_based_activity = TimeBasedActivityShadow(
            activity_ptr_id=initiative_id,
            review=False,
        )
        time_based_activities.append(time_based_activity)

        date_activity = DateActivityShadow(
            timebasedactivity_ptr_id=initiative_id,
            slot_selection='free',
        )
        date_activities.append(date_activity)

        city_id = row.find("field[@name='city_id']").text
        if city_id:
            city_id = 100 + int(city_id)
            city = Activity.segments.through(
                activity_id=initiative_id,
                segment_id=city_id
            )
            cities.append(city)

        contributor = Contributor(
            id=initiative_id,
            user=owner,
            activity=activity,
            status='succeeded',
            polymorphic_ctype_id=organizer_type
        )
        contributors.append(contributor)
        organizer = OrganizerShadow(
            contributor_ptr_id=initiative_id,
        )
        organizers.append(organizer)

        contribution = Contribution(
            id=initiative_id,
            contributor=contributor,
            polymoprhic_ctype_id=effort_type
        )
        contributions.append(contribution)
        effort_contribution = EffortContributionShadow(
            contribution_ptr_id=initiative_id,
            contribution_type='organizer'
        )
        effort_contributions.append(effort_contribution)

    print("Writing contacts")
    OrganizationContact.objects.bulk_create(contacts)
    update_sequence('organizations_organizationcontact')

    print("Writing initiative images")
    # bulk_create screws op uuid
    for i in images:
        i.save()

    print("Writing initiatives")
    Initiative.objects.bulk_create(initiatives)
    update_sequence('initiatives_initiative')

    print("Writing activities")
    Activity.objects.bulk_create(activities)
    TimeBasedActivityShadow.objects.bulk_create(time_based_activities)
    DateActivityShadow.objects.bulk_create(date_activities)
    update_sequence('activities_activity')

    print("Writing initiative cities (segments)")
    Activity.segments.through.objects.bulk_create(cities)

    print("Writing organizers & contributions")
    Contributor.objects.bulk_create(contributors)
    OrganizerShadow.objects.bulk_create(organizers)
    Contribution.objects.bulk_create(contributions)
    EffortContributionShadow.objects.bulk_create(effort_contributions)


def import_initiative_themes(rows):
    initiatives = []
    for row in rows:
        initiative_id = row.find("field[@name='activity_id']").text
        initiative = Initiative.objects.get(id=initiative_id)
        initiative.theme_id = row.find("field[@name='activity_type_id']").text
        initiatives.append(initiative)
    Initiative.objects.bulk_update(initiatives, ['theme_id'])


def import_slots(rows):
    slots = []
    for row in rows:
        slot = DateActivitySlot(
            is_online=False
        )
        for k in mapping['slot']:
            v = mapping['slot'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            slot.__setattr__(k, value)
        slot.duration = timedelta(hours=float(row.find("field[@name='duration']").text.replace('-', '')))
        slot.start = add_tz(slot.start)
        if slot.start + slot.duration < now():
            slot.status = 'succeeded'
        else:
            slot.status = 'open'
        slot.created = add_tz(slot.created)
        slots.append(slot)
    DateActivitySlot.objects.bulk_create(slots)
    update_sequence('time_based_dateactivityslot')


def import_slot_participants(rows):
    DateParticipantShadow = create_model(DateParticipant)
    date_participant_type = ContentType.objects.get_for_model(DateParticipant).id
    TimeContributionShadow = create_model(TimeContribution)
    time_contribution_type = ContentType.objects.get_for_model(TimeContribution).id

    contributors = []
    date_participants = []
    slot_participants = []
    contributions = []
    time_contributions = []

    print('Reading participants')
    for row in rows:
        contributor_id = row.find("field[@name='id']").text
        shift_id = row.find("field[@name='shift_id']").text
        user_id = row.find("field[@name='user_id']").text
        status = row.find("field[@name='status']").text
        if status == 'no-show':
            status = 'cancelled'
        elif status == 'planned':
            status = 'accepted'
        else:
            status = 'succeeded'
        activity = DateActivity.objects.get(slots__id=shift_id)
        contributor_id = 200000 + int(contributor_id)
        contributor = Contributor(
            id=contributor_id,
            user_id=user_id,
            activity_id=activity.id,
            polymorphic_ctype_id=date_participant_type
        )
        contributors.append(contributor)

        date_participant = DateParticipantShadow(
            contributor_ptr_id=contributor_id
        )
        date_participants.append(date_participant)

        slot_participant = SlotParticipant(
            participant_id=contributor_id,
            slot_id=shift_id,
            status=status
        )
        slot_participants.append(slot_participant)

        contribution_id = 100000 + int(contributor_id)
        contribution = Contribution(
            id=contribution_id,
            contributor=contributor,
            polymorphic_ctype_id=time_contribution_type
        )
        contributions.append(contribution)

        time_contribution = TimeContributionShadow(
            contribution_ptr_id=contribution_id,
            contribution_type='date',
            slot_participant=slot_participant,
            value=timedelta(hours=1)
        )
        time_contributions.append(time_contribution)

    print('Writing participants')
    Contributor.objects.bulk_create(contributors)
    DateParticipantShadow.objects.bulk_create(date_participants)

    print('Writing slot participants')
    SlotParticipant.objects.bulk_create(slot_participants)
    update_sequence('activities_contributor')

    print('Writing time contributions')
    Contribution.objects.bulk_create(contributions)
    TimeContributionShadow.objects.bulk_create(time_contributions)
    update_sequence('activities_contribution')


def import_activity_location(rows):
    slots = []
    initiatives = []
    for row in rows:
        address = "{}, {}".format(
            row.find("field[@name='street']").text,
            row.find("field[@name='city']").text
        )
        location, _c = Geolocation.objects.get_or_create(
            country_id=nld_id,
            locality=row.find("field[@name='city']").text,
            street=row.find("field[@name='street']").text,
            position=None,
            defaults={
                'postal_code': row.find("field[@name='zipcode']").text,
                'formatted_address': address
            }
        )
        organization_id = row.find("field[@name='social_institution_id']").text
        activity_id = row.find("field[@name='activity_id']").text
        initiative_id = activity_id
        activity_slots = list(DateActivitySlot.objects.filter(activity_id=activity_id).all())
        initiative = Initiative.objects.get(id=initiative_id)
        initiative.place = location
        initiative.organization_id = organization_id
        initiatives.append(initiative)
        for slot in activity_slots:
            slot.location = location
        slots += activity_slots
    print("Writing slot locations")
    DateActivitySlot.objects.bulk_update(slots, ['location_id'])
    print("Writing initiative locations")
    Initiative.objects.bulk_update(initiatives, ['place_id', 'organization_id'])
    update_sequence('geo_geolocation')


def import_users(rows):
    # Get admin user so we can save it later with a new ID
    admin, _c = Member.objects.get_or_create(
        email='admin@example.com',
        is_superuser=True,
    )
    admin.id = None
    Member.objects.all().delete()
    update_sequence('members_member')

    staff = Group.objects.get(name='Staff')
    authenticated = Group.objects.get(name='Authenticated')
    users = []
    segments = []
    locations = []
    for row in rows:

        user = Member()
        for k in mapping['user']:
            v = mapping['user'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            user.__setattr__(k, value)
        user.password = 'bcrypt${}'.format(user.password)
        if not user.email:
            user.email = 'user{}@example.com'.format(user.id)
        user.username = user.email
        if '@nlcares.nl' in user.email or '@sonnyspaan.nl' in user.email:
            user.is_staff = True
        if row.find("field[@name='active']").text != '0':
            user.is_active = True
        user.created = add_tz(user.created)

        segment_id = row.find("field[@name='reference_id']").text
        segment_ids = Segment.objects.values_list('id', flat=True)
        if segment_id and int(segment_id) in segment_ids:
            segment = Member.segments.through(
                member=user,
                segment_id=segment_id
            )
            segments.append(segment)

        city_id = row.find("field[@name='volunteer_city']").text
        if city_id:
            city_id = 100 + int(city_id)
            segment = Member.segments.through(
                member=user,
                segment_id=city_id
            )
            segments.append(segment)

        city = row.find("field[@name='city']").text
        street = row.find("field[@name='street']").text
        houseno_att = row.find("field[@name='houseno_att']").text
        if houseno_att:
            street = "{} {}".format(street, houseno_att)
        zipcode = row.find("field[@name='zipcode']").text
        location = Place(
            country_id=nld_id,
            street=street,
            locality=city,
            postal_code=zipcode,
            content_object=user
        )
        locations.append(location)
        users.append(user)

    print("Writing users")
    Member.objects.bulk_create(users)
    authenticated.user_set.add(*Member.objects.all())
    staff.user_set.add(*Member.objects.filter(is_staff=True).all())
    update_sequence('members_member')
    admin.save()

    print("Writing user segments")
    Member.segments.through.objects.bulk_create(segments)

    print("Writing user locations")
    Place.objects.bulk_create(locations)

    # Create some users we need
    nlcares = Member.objects.create(
        first_name='NL Cares',
        last_name='Office',
        email='info@nlcares.nl',
        username='info@nlcares.nl',
        is_staff=True,
        is_active=True
    )
    authenticated.user_set.add(nlcares)
    staff.user_set.add(nlcares)


def import_segments(rows):
    segments = []
    reference = SegmentType.objects.create(name='Reference', slug='reference')
    for row in rows:
        segment = Segment(
            type=reference,
            alternate_names=[]
        )
        for k in mapping['segment']:
            v = mapping['segment'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            segment.__setattr__(k, value)
        segments.append(segment)
    Segment.objects.bulk_create(segments)


def import_organizations(rows):
    orgs = []
    for row in rows:
        org = Organization(
            id=row.find("field[@name='id']").text,
            name=row.find("field[@name='name']").text,
            slug=row.find("field[@name='slug']").text,
        )
        orgs.append(org)
    print("Writing partner organizations")
    Organization.objects.bulk_create(orgs)
    update_sequence('organizations_organization')


def import_cities(rows):
    city_segment = SegmentType.objects.create(name='City', slug='city')
    for row in rows:
        id = 100 + int(row.find("field[@name='id']").text)
        city = Segment.objects.create(
            type=city_segment,
            id=id,
            alternate_names=[],
            name=row.find("field[@name='name']").text
        )
        city.save()


def run(*args):
    tne = Client.objects.get(schema_name='nlcares')
    with LocalTenant(tne):
        if Country.objects.count() < 10:
            print('RUN ./manage.py tenant_command -s nlcares loaddata geo_data')
            return
        properties.SEND_MAIL = False
        properties.SEND_WELCOME_MAIL = False
        properties.CELERY_MAIL = False

        print("Reading XML")
        root = ET.parse('./nlcares.xml').getroot()

        # [districts] >> geolocations
        print("Importing cities")
        rows = root.find('database').find('table_data[@name="cities"]').findall('row')
        import_cities(rows)

        # [references] >> Segments
        print("Importing references/segments")
        rows = root.find('database').find('table_data[@name="references"]').findall('row')
        import_segments(rows)

        # Import users
        print("Importing users")
        rows = root.find('database').find('table_data[@name="users"]').findall('row')
        import_users(rows)

        # Import initiatives & Activities
        print("Importing initiatives")
        rows = root.find('database').find('table_data[@name="activities"]').findall('row')
        import_initiatives(rows)

        # [social_institutions] >> Partner organizations
        print("Importing partner organizations")
        rows = root.find('database').find('table_data[@name="social_institutions"]').findall('row')
        import_organizations(rows)

        # Import themes
        print("Importing themes")
        rows = root.find('database').find('table_data[@name="activity_types"]').findall('row')
        import_themes(rows)

        # Import Initiative theme
        print("Importing activity themes")
        rows = root.find('database').find('table_data[@name="activity_activity_type"]').findall('row')
        import_initiative_themes(rows)

        # Import slots
        print("Importing slots")
        rows = root.find('database').find('table_data[@name="shifts"]').findall('row')
        import_slots(rows)

        # Import activity/slot location
        print("Importing slot locations")
        rows = root.find('database').find('table_data[@name="events"]').findall('row')
        import_activity_location(rows)

        # [shift_user] / DateParticipant + SlotParticipants + Contribution
        print("Importing slot participants")
        rows = root.find('database').find('table_data[@name="shift_user"]').findall('row')
        import_slot_participants(rows)

        # activity contacts > partner org contacts
        print("FIX ME: SET VALUE for TIME DURATION")

        print("FIX ME: CHANGE STATUSES FOR SLOTS")
        print("FIX ME: CHANGE STATUSES FOR SLOT PARTICIPANTS")
        print("FIX ME: CHANGE STATUSES FOR CONTRIBUTIONS")

        print("FIX ME: CHANGE STATUSES FOR PARTICIPANTS")
        print("FIX ME: CHANGE STATUSES FOR ACTIVITIES")
        print("FIX ME: CHANGE STATUSES FOR INITIATIVES")


"""
Clear all tables:

delete from time_based_timecontribution;
delete from time_based_slotparticipant;
delete from time_based_dateparticipant;
delete from activities_contributor;

delete from activities_organizer;
delete from activities_effortcontribution;
delete from activities_contribution;
delete from activities_contributor;

delete from time_based_dateactivityslot;
delete from time_based_dateactivity;
delete from time_based_timebasedactivity;
delete from activities_activity;

delete from initiatives_initiative_categories;
delete from categories_category_translation;
delete from categories_category;
delete from initiatives_initiative_activity_managers;
delete from initiatives_initiative;
delete from initiatives_theme_translation;
delete from initiatives_theme;

delete from geo_geolocation;

delete from files_image;
delete from notifications_message;
delete from members_member_groups;
delete from follow_follow;
delete from organizations_organizationcontact;
delete from organizations_organization;
delete from members_useractivity;
delete from activities_effortcontribution;
delete from activities_organizer;
delete from django_admin_log;
delete from activities_activity_segments;
delete from members_member_segments;
delete from segments_segment;
delete from segments_segmenttype;
delete from geo_place;
delete from members_member_favourite_themes;
delete from members_member where email != 'admin@example.com';

"""
