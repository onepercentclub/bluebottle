from django.contrib import admin
from bluebottle.votes.models import Vote


class VoteAdmin(admin.ModelAdmin):
    raw_id_fields = ('voter', 'project')

admin.site.register(Vote, VoteAdmin)
