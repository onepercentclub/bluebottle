# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(verbose_name='Amount')),
                ('currency', models.CharField(default=b'EUR', max_length=3, verbose_name='Currency')),
                ('language', models.CharField(choices=[(b'en', 'English'), (b'nl', 'Dutch')], default=b'en', max_length=2, verbose_name='Language')),
                ('message', models.TextField(blank=True, default=b'', max_length=500, verbose_name='Message')),
                ('code', models.CharField(blank=True, default=b'', max_length=100, verbose_name='Code')),
                ('status', models.CharField(choices=[(b'new', 'New'), (b'paid', 'Paid'), (b'cancelled', 'Cancelled'), (b'cashed', 'Cashed'), (b'cashed_by_proxy', 'Cashed by us')], db_index=True, default=b'new', max_length=20, verbose_name='Status')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='Updated')),
                ('sender_email', models.EmailField(max_length=254, verbose_name='Sender email')),
                ('sender_name', models.CharField(blank=True, default=b'', max_length=100, verbose_name='Sender name')),
                ('receiver_email', models.EmailField(max_length=254, verbose_name='Receiver email')),
                ('receiver_name', models.CharField(blank=True, default=b'', max_length=100, verbose_name='Receiver name')),
                ('order', models.ForeignKey(help_text='The order that bought this voucher', null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.Order', verbose_name='Order')),
                ('receiver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='casher', to=settings.AUTH_USER_MODEL, verbose_name='Receiver')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='buyer', to=settings.AUTH_USER_MODEL, verbose_name='Sender')),
            ],
        ),
        migrations.CreateModel(
            name='VoucherPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='payments.Payment')),
                ('voucher', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='payments_voucher.Voucher', verbose_name='Voucher')),
            ],
            options={
                'ordering': ('-created', '-updated'),
                'verbose_name': 'Voucher Payment',
                'verbose_name_plural': 'Voucher Payments',
            },
            bases=('payments.payment',),
        ),
    ]
