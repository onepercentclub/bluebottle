# Data work moved to scripts/get_geofeatures.py (run per tenant via runscript).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0047_auto_20260420_1702'),
    ]

    operations = []
