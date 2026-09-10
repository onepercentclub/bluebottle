from django.db import migrations, models
import django.db.models.deletion


def set_primary_geofeatures(apps, schema_editor):
    Geolocation = apps.get_model('geo', 'Geolocation')
    GeoFeature = apps.get_model('geo', 'GeoFeature')

    for geolocation in Geolocation.objects.exclude(
        mapbox_id__isnull=True
    ).exclude(
        mapbox_id=''
    ):
        primary = GeoFeature.objects.filter(mapbox_id=geolocation.mapbox_id).first()
        if primary:
            Geolocation.objects.filter(pk=geolocation.pk).update(geofeature_id=primary.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0042_remove_geofeature_place_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='geolocation',
            name='geofeature',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='primary_geolocations',
                to='geo.geofeature',
            ),
        ),
        migrations.RunPython(set_primary_geofeatures, migrations.RunPython.noop),
    ]
