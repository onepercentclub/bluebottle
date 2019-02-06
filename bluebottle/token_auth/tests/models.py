from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class TestUser(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    email = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    remote_id = models.CharField(_('remote_id'), max_length=75, blank=True, null=True)
    is_active = models.BooleanField('is active', default=True)
