"""
Main URLs file for BlueBottle itself. It joins the i18n URL patterns with the
rest. It can be seen as an example for implementing those projects which use
BlueBottle.

Django does not permit to directly include i18n patterns into non-i18n ones,
so we create a new i18n pattern to append to the existent one and there we
include the i18n related urls.
"""
from __future__ import absolute_import

from django.urls import path
from django.urls import include
from django.conf.urls.i18n import i18n_patterns

from .core import urlpatterns

urlpatterns += i18n_patterns(
    path('', include('bluebottle.urls.i18n_urls')),
)
