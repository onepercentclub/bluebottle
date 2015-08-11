from django.contrib import admin
from django.conf.urls import patterns
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from bluebottle.bb_accounts.admin import BlueBottleUserAdmin
from bluebottle.votes.models import Vote

from .models import Member


class MemberVotesInline(admin.TabularInline):
    model = Vote
    readonly_fields = ('project', 'created')
    fields = ('project', 'created',)
    extra = 0


class MemberAdmin(BlueBottleUserAdmin):
    inlines = BlueBottleUserAdmin.inlines + [MemberVotesInline]

    def __init__(self, *args, **kwargs):
        super(MemberAdmin, self).__init__(*args, **kwargs)

        self.list_display = ('email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'is_active', 'login_as_link')

    def get_urls(self):
        urls = super(MemberAdmin, self).get_urls()

        extra_urls = patterns('',
                              (r'^login-as/(?P<user_id>\d+)/$',
                               self.admin_site.admin_view(self.login_as_redirect)),
                              )
        return extra_urls + urls

    def login_as_redirect(self, *args, **kwargs):
        user = Member.objects.get(id=kwargs.get('user_id', None))
        url = "/go/login-with/{0}".format(user.get_jwt_token())

        return HttpResponseRedirect(url)

    def login_as_link(self, obj):
        return "<a target='_blank' href='{0}members/member/login-as/{1}/'>{2}</a>".format(reverse('admin:index'), obj.pk, 'Login as user')

    login_as_link.allow_tags = True

admin.site.register(Member, MemberAdmin)
