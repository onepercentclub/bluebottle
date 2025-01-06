# Generated by Django 3.2.20 on 2024-10-09 12:13

from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0035_set_alternate_names'),
        ('funding', '0066_auto_20240919_0850'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='donor',
            options={'verbose_name': 'Donation', 'verbose_name_plural': 'Donations'},
        ),
        migrations.AlterModelOptions(
            name='legacypayment',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='moneycontribution',
            options={'verbose_name': 'Donation', 'verbose_name_plural': 'Contributions'},
        ),
        migrations.AlterModelOptions(
            name='paymentprovider',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='payoutaccount',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AddField(
            model_name='fundingplatformsettings',
            name='public_accounts',
            field=models.BooleanField(default=False, verbose_name='Allow users to select account from list of public accounts'),
        ),
        migrations.AddField(
            model_name='payoutaccount',
            name='public',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='budgetline',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
        migrations.AlterField(
            model_name='donor',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
        migrations.AlterField(
            model_name='funding',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.country'),
        ),
        migrations.AlterField(
            model_name='funding',
            name='target_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
        migrations.AlterField(
            model_name='fundraiser',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
        migrations.AlterField(
            model_name='paymentcurrency',
            name='code',
            field=models.CharField(default='EUR', max_length=3),
        ),
        migrations.AlterField(
            model_name='reward',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
    ]
