# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

import bluebottle.utils.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('orders', '0001_initial'),
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[(b'created', 'Created'), (b'started', 'Started'), (b'cancelled', 'Cancelled'), (b'pledged', 'Pledged'), (b'authorized', 'Authorized'), (b'settled', 'Settled'), (b'charged_back', 'Charged_back'), (b'refunded', 'Refunded'), (b'failed', 'Failed'), (b'unknown', 'Unknown')], default=b'created', max_length=50)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='Updated')),
                ('closed', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Closed')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=16, verbose_name='Amount')),
                ('transaction_fee', models.DecimalField(decimal_places=2, help_text='Bank & transaction fee, withheld by payment provider.', max_digits=16, null=True, verbose_name='Transaction Fee')),
                ('payment_method', models.CharField(blank=True, default=b'', max_length=20)),
                ('integration_data', django_extensions.db.fields.json.JSONField(blank=True, max_length=5000, verbose_name='Integration data')),
            ],
            bases=(models.Model, ),
        ),
        migrations.CreateModel(
            name='OrderPaymentAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, choices=[(b'redirect', 'Redirect'), (b'popup', 'Popup')], max_length=20, verbose_name='Authorization action type')),
                ('method', models.CharField(blank=True, choices=[(b'get', 'GET'), (b'post', 'POST')], max_length=20, verbose_name='Authorization action method')),
                ('url', models.CharField(blank=True, max_length=2000, verbose_name='Authorization action url')),
                ('payload', models.CharField(blank=True, max_length=5000, verbose_name='Authorization action payload')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[(b'created', 'Created'), (b'started', 'Started'), (b'cancelled', 'Cancelled'), (b'pledged', 'Pledged'), (b'authorized', 'Authorized'), (b'settled', 'Settled'), (b'charged_back', 'Charged_back'), (b'refunded', 'Refunded'), (b'failed', 'Failed'), (b'unknown', 'Unknown')], default=b'started', max_length=50)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='Updated')),
                ('order_payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='payments.OrderPayment')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_payments.payment_set+', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-created', '-updated'),
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='Updated')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.Payment')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_payments.transaction_set+', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-created', '-updated'),
            },
        ),
        migrations.AddField(
            model_name='orderpayment',
            name='authorization_action',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.OrderPaymentAction', verbose_name='Authorization action'),
        ),
        migrations.AddField(
            model_name='orderpayment',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_payments', to='orders.Order'),
        ),
        migrations.AddField(
            model_name='orderpayment',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
