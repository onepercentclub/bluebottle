from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.shortcuts import render_to_response
from django.template.context import RequestContext



urlpatterns = patterns('',
    # The api urls are in the / url namespace so that they're not redirected to /en/.
    url(r'^api/users/', include('bluebottle.members.urls.api')),
    url(r'^api/bb_organizations/', include('bluebottle.bb_organizations.urls.api')),
    url(r'^api/bb_projects/', include('bluebottle.bb_projects.urls.api')),
    url(r'^api/fundraisers/', include('bluebottle.bb_fundraisers.urls.api')),
    url(r'^api/bb_tasks/', include('bluebottle.bb_tasks.urls.api')),
    url(r'^api/geo/', include('bluebottle.geo.urls.api')),
    url(r'^api/contact/', include('bluebottle.contact.urls.api')),
    url(r'^api/news/', include('bluebottle.news.urls.api')),
    url(r'^api/pages/', include('bluebottle.pages.urls.api')),
    url(r'^api/quotes/', include('bluebottle.quotes.urls.api')),
    url(r'^api/slides/', include('bluebottle.slides.urls.api')),
    url(r'^api/utils/', include('bluebottle.utils.urls.api')),
    url(r'^api/wallposts/', include('bluebottle.wallposts.urls.api')),
    url(r'^api/terms/', include('bluebottle.terms.urls.api')),
    url(r'^api/metadata/', include('bluebottle.utils.urls.api')),

    url(r'^api/orders/', include('bluebottle.bb_orders.urls.api')),
    url(r'^api/donations/', include('bluebottle.bb_donations.urls.api')),
    url(r'^api/order_payments/', include('bluebottle.payments.urls.order_payments_api')),
    url(r'^api/payments/', include('bluebottle.payments.urls.api')),

    url(r'^payments_mock/', include('bluebottle.payments_mock.urls.core')),
    url(r'^payments_docdata/', include('bluebottle.payments_docdata.urls.core')),

    url(r'^documents/', include('bluebottle.utils.urls.main')),
    url(r'^embed/', include('bluebottle.widget.urls.core')),

    # JSON Web Token based authentication for Django REST framework
    url(r'^api/token-auth/', 'rest_framework_jwt.views.obtain_jwt_token'),

)

# Nicely parse 500 errors so we get semantic messages in tests.
def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response

urlpatterns += patterns(
    'loginas.views',
    url(r"^login/user/(?P<user_id>.+)/$", "user_login", name="loginas-user-login"),
)

js_info_dict = {
    'packages': ('apps.bb_accounts', 'apps.bb_projects'),
}

urlpatterns += patterns(
    '',
    (r'^js$', 'django.views.i18n.javascript_catalog'),
)

# Serve django-staticfiles (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

# Serve media files (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#django.conf.urls.static.static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
