# Generated by Django 2.2.24 on 2022-04-06 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0054_auto_20220405_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='accepted_invite',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accepted_contributors', to='activities.Invite'),
        ),
        migrations.AlterField(
            model_name='contributor',
            name='invite',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contributors', to='activities.Invite'),
        ),
    ]