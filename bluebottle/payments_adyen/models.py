from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django.utils.translation import ugettext as _
from django.db import models
from django_countries.fields import CountryField

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


class AdyenPaymentMetaData(models.Model):

    payment = models.ForeignKey('payments.Payment')

    customer_id = models.PositiveIntegerField(default=0)  # Defaults to 0 for anonymous.
    email = models.EmailField(max_length=254, default='')
    first_name = models.CharField(max_length=200, default='')
    last_name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, default='')
    postal_code = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=200, default='')
    country = CountryField()
    language = models.CharField(max_length=2, default='en')


class AdyenPaymentTransaction(models.Model):

    payment = models.ForeignKey('payments.Payment')

    status = models.CharField(_("status"), max_length=30, default='NEW')

    payment_method = models.CharField(max_length=60, default='', blank=True)

    created = CreationDateTimeField(_("created"))
    updated = ModificationDateTimeField(_("updated"))


class AdyenPaymentStatusChange(models.Model):

    payment = models.ForeignKey('AdyenPaymentTransaction')

    old_status = models.CharField(_("status"), max_length=30, default='NEW')
    new_status = models.CharField(_("status"), max_length=30, default='NEW')

    created = CreationDateTimeField(_("created"))
