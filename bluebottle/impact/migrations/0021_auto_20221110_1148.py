# Generated by Django 2.2.24 on 2022-11-10 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0020_auto_20211001_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='impacttype',
            name='icon',
            field=models.CharField(blank=True, choices=[('people', 'People'), ('time', 'Time'), ('money', 'Money'), ('trees', 'Trees'), ('animals', 'Animals'), ('jobs', 'Jobs'), ('co2', 'C02'), ('water', 'Water'), ('plastic', 'plastic'), ('food', 'Food'), ('task', 'Task'), ('task-completed', 'Task completed'), ('event', 'Event'), ('event-completed', 'Event completed'), ('funding', 'Funding'), ('funding-completed', 'Funding completed')], max_length=20, null=True, verbose_name='icon'),
        ),
    ]
