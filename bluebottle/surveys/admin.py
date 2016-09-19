from django.contrib import admin

from bluebottle.surveys.models import Survey, Question


class QuestionAdminInline(admin.StackedInline):

    model = Question
    readonly_fields = ('specification', 'remote_id', 'properties')

    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    can_delete = False


class SurveyAdmin(admin.ModelAdmin):
    model = Survey
    inlines = [QuestionAdminInline]

admin.site.register(Survey, SurveyAdmin)

