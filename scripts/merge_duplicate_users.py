from django.db.models.functions import Lower
from django.db.models import Count

from bluebottle.members.models import Member

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.activities.models import Activity, Contributor
from bluebottle.initiatives.models import Initiative
from bluebottle.wallposts.models import Wallpost


for client in Client.objects.all():
    with LocalTenant(client):
        duplicate = Member.objects.annotate(
            lower=Lower('email')
        ).values('lower').annotate(count=Count('lower')).filter(count__gt=1)
        for result in duplicate:
            first, *duplicates = Member.objects.filter(email__iexact=result['lower']).order_by('date_joined')
            for duplicate in duplicates:
                for activity in Activity.objects.filter(owner=duplicate):
                    activity.owner = first
                    activity.execute_triggers(send_messages=False)
                    activity.save()

                for contributor in Contributor.objects.filter(user=duplicate):
                    contributor.user = first
                    contributor.execute_triggers(send_messages=False)
                    contributor.save()

                for initiative in Initiative.objects.filter(owner=duplicate):
                    initiative.owner = first
                    initiative.execute_triggers(send_messages=False)
                    initiative.save()

                for wallpost in Wallpost.objects.filter(author=duplicate):
                    wallpost.author = first
                    wallpost.save()

                duplicate.anonymize()
                duplicate.email = 'merged-{}-{}@example.com'.format(first.pk, duplicate.pk)
                duplicate.save()
