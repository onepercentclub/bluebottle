from datetime import date
import xlsxwriter

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding.models import Funding, Donor
from bluebottle.geo.models import Location


OFFICE_NAME = 'Segou'
TARGET = 328000
DEADLINE = date(2022, 8, 13)

def run(*args):
    tne = Client.objects.get(client_name='nexteconomy')

    with LocalTenant(tne, clear_tenant=True):
        result = []

        location = Location.objects.get(name=OFFICE_NAME)

        campaigns = Funding.objects.filter(
            initiative__location__name=OFFICE_NAME,
            deadline__date=DEADLINE,
            status__in=('succeeded', 'partially_funded')
        )

        for campaign in campaigns:
            donors = campaign.contributors.instance_of(
                Donor
            ).filter(
                status='succeeded'
            ).order_by(
                'created'
            )

            total = 0
            for donor in donors:
                total += donor.amount.amount
                
                if total > TARGET:
                    result.append({
                        'id': campaign.id, 
                        'title': campaign.title, 
                        'status': campaign.status, 
                        'target reached': str(donor.created), 
                    })
                    break

            
        workbook = xlsxwriter.Workbook(f'TNE-{location.name}-{DEADLINE}.xlsx', {'remove_timezone': True})
        worksheet = workbook.add_worksheet()

        worksheet.write_row(0, 0, result[0].keys())

        for (index, row) in enumerate(result):
            worksheet.write_row(index + 1, 0, row.values())

        workbook.close()

        

