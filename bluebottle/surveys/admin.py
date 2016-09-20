from django.contrib import admin

from bluebottle.surveys.models import Survey, Question, Response, Answer


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


class AnswerAdminInline(admin.TabularInline):
    model = Answer

    readonly_fields = ('question', 'value', )
    fields = readonly_fields
    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    can_delete = False


class ResponseAdmin(admin.ModelAdmin):
    model = Response
    inlines = [AnswerAdminInline]

    readonly_fields = ('remote_id', 'specification', 'survey',
                       'project', 'task')

    list_display = ('survey', 'submitted', 'answer_count')

    def answer_count(self, obj):
        return obj.answer_set.count()

admin.site.register(Response, ResponseAdmin)

