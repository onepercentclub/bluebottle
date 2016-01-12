from django.contrib import admin


from .models import Reward


class RewardAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'project')
    date_hierarchy = 'publication_date'
    search_fields = ('title', 'description')
    model = Reward

    raw_id_fields = ('project',)

    fields = ('title', 'description', 'project')

admin.site.register(Reward, RewardAdmin)
