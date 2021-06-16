import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Point
from django.db import connection
from django.utils.timezone import now

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation, Country
from bluebottle.initiatives.models import Theme, Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import DateActivity, DateActivitySlot, SlotParticipant, DateParticipant

ams = pytz.timezone('Europe/Amsterdam')


def add_tz(date):
    if not date:
        return date
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    if date.tzinfo:
        return date
    return ams.localize(date)


status_mapping = {
    'In progress': 'open',
    'Planned': 'open',
    'completed': 'succeeded',
    'confirmed': 'succeeded',
    'no-show': 'cancelled',
}

mapping = {
    'initiative': {
        'id': 'id',
        'title': 'name_nl',
        'slug': 'slug_nl',
        'story': 'description_nl',
        'created': 'created_at',
    },
    'activity': {
        'id': 'id',
        'initiative_id': 'id',
        'title': 'name_nl',
        'slug': 'slug_nl',
        'description': 'description_nl',
        'created': 'created_at',
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
    },
    'location': {
        'id': 'id',
        'locality': 'city',
        'formatted_address': 'name',
        'street': 'street',
        'postal_code': 'zipcode',
        'created': 'created_at',
    }
}


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


def import_initiatives(rows):
    initiatives = []
    activities = []
    for row in rows:
        initiative = Initiative(
            status='approved'
        )
        initiative_id = row.find("field[@name='id']").text
        email = row.find("field[@name='contact_email']").text or 'initiator{}@example.com'.format(initiative_id)
        first_name = row.find("field[@name='contact_firstname']").text or 'Nomen'
        last_name = row.find("field[@name='contact_lastname']").text or 'Nescio'
        owner, _c = Member.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            })
        for k in mapping['initiative']:
            v = mapping['initiative'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            initiative.__setattr__(k, value)
            initiative.owner = owner

            # image_url = row.find("field[@name='image_url']").text
            # if image_url:
            #     try:
            #         name, _ = urlretrieve(image_url)
            #         image = Image(
            #             owner=owner
            #         )
            #         image.file.save("image_%s" % initiative.id, File(open(name, 'rb')))
            #         image.save()
            #         initiative.image = image
            #     except HTTPError:
            #         pass
            #     except URLError:
            #         pass
            initiative.created = add_tz(initiative.created)
        initiatives.append(initiative)

        activity = DateActivity()
        for k in mapping['activity']:
            v = mapping['activity'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            activity.__setattr__(k, value)
            activity.status = 'open'
            activity.created = add_tz(activity.created)
            activity.owner = owner
        activities.append(activity)
    print("Writing initiatives")
    Initiative.objects.bulk_create(initiatives)
    print("Writing activities")
    for activity in activities:
        activity.save()


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


def import_slot_participants(rows):
    slot_participants = []
    print('Writing participants')
    for row in rows:
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
        participant, _c = DateParticipant.objects.get_or_create(user_id=user_id, activity=activity)
        slot_participant = SlotParticipant(
            participant=participant,
            slot_id=shift_id,
            status=status
        )
        slot_participants.append(slot_participant)
    print('Writing slot participants')
    SlotParticipant.objects.bulk_create(slot_participants)


def import_activity_location(rows):
    locations = []
    slots = []
    nld = Country.objects.get(alpha2_code='NL')
    for row in rows:
        location = Geolocation(
            country=nld,
            position=Point(0, 0)
        )
        for k in mapping['location']:
            v = mapping['location'][k]
            value = row.find("field[@name='{}']".format(v)).text or ''
            location.__setattr__(k, value)
        location.position = 'point(5.2793703 52.2129919)'
        activity_id = row.find("field[@name='activity_id']").text
        location_id = row.find("field[@name='id']").text
        slots += list(DateActivitySlot.objects.filter(activity_id=activity_id).all())
        for slot in slots:
            slot.location_id = location_id
        locations.append(location)
    Geolocation.objects.bulk_create(locations)
    DateActivitySlot.objects.bulk_update(slots, ['location_id'])


def import_users(rows):
    staff = Group.objects.get(name='Staff')
    users = []
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
        users.append(user)
    Member.objects.bulk_create(users)
    for mem in Member.objects.filter(is_staff=True).all():
        staff.user_set.add(mem)
    update_sequence('members_member')


def run(*args):
    tne = Client.objects.get(schema_name='nlcares')
    with LocalTenant(tne):
        if Country.objects.count() < 10:
            print('RUN ./manage.py tenant_command -s nlcares loaddata geo_data')
            return
        properties.SEND_MAIL = False
        properties.SEND_WELCOME_MAIL = False
        properties.CELERY_MAIL = False

        update_sequence('members_member')

        print("Reading XML")
        root = ET.parse('./nlcares.xml').getroot()

        # # Import users
        # print("Importing users")
        # rows = root.find('database').find('table_data[@name="users"]').findall('row')
        # import_users(rows)
        #
        # print("Importing themes")
        # # Import themes
        # rows = root.find('database').find('table_data[@name="activity_types"]').findall('row')
        # import_themes(rows)
        #
        # # Import initiatives & Activities
        # print("Importing initiatives")
        # rows = root.find('database').find('table_data[@name="activities"]').findall('row')
        # import_initiatives(rows)
        #
        # # Import Initiative theme
        # print("Importing slot locations")
        # rows = root.find('database').find('table_data[@name="activity_activity_type"]').findall('row')
        # import_initiative_themes(rows)
        #
        # # Import slots
        # print("Importing slots")
        # rows = root.find('database').find('table_data[@name="shifts"]').findall('row')
        # import_slots(rows)
        #
        # # Import activity/slot location
        # print("Importing slot locations")
        # rows = root.find('database').find('table_data[@name="events"]').findall('row')
        # import_activity_location(rows)

        # [shift_user] / DateParticipant + SlotParticipants + Contribution
        print("Importing slot participants")
        rows = root.find('database').find('table_data[@name="shift_user"]').findall('row')
        import_slot_participants(rows)

        # [references] / >> Segments

        # [cities] / ??

        # [city_districts] / ??

        # [social_institutions] / ?? Partner orgs?
        #
        # activity contacts > partner org contacts
        # nl cares admin > activity owner

        # Save city + city districts > geolocation


"""
Clear all tables:

delete from time_based_timecontribution;
delete from time_based_slotparticipant;
delete from time_based_dateparticipant;

delete from activities_organizer;
delete from activities_effortcontribution;
delete from activities_contribution;
delete from activities_contributor;

delete from time_based_dateactivityslot;
delete from time_based_dateactivity;
delete from time_based_timebasedactivity;
delete from activities_activity;

delete from initiatives_initiative;
delete from geo_geolocation;

delete from initiatives_theme_translation;
delete from initiatives_theme;
delete from files_image;
delete from notifications_message; delete from members_member_groups; delete from members_member;

"""
