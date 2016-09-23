from django.contrib import admin

from bluebottle.surveys.models import Survey, Question, Response, Answer, AggregateAnswer


class QuestionAdminInline(admin.StackedInline):

    model = Question
    readonly_fields = ('remote_id', 'type', 'properties', 'title', 'sub_questions')
    fields = readonly_fields + ('display', 'display_title',
                                'display_style', 'aggregation')

    extra = 0


    def sub_questions(self, obj):
        return [sub.title for sub in obj.subquestion_set.all()]


    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    can_delete = False


class SurveyAdmin(admin.ModelAdmin):
    model = Survey
    readonly_fields = ('title', 'link', 'created', 'updated')
    fields = ('remote_id', ) + readonly_fields
    list_display = ('title', 'created')
    inlines = [QuestionAdminInline]

    actions = ['synchronize_surveys']


    def synchronize_surveys(self, request, queryset):
        for survey in queryset:
            survey.synchronize()

admin.site.register(Survey, SurveyAdmin)


class AnswerAdminInline(admin.TabularInline):
    model = Answer

    readonly_fields = ('question', 'value', 'options')
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
    raw_id_fields = ('project', 'task')

    readonly_fields = ('remote_id', 'survey')

    list_display = ('survey', 'submitted', 'project', 'task', 'answer_count')

    def answer_count(self, obj):
        return obj.answer_set.count()

admin.site.register(Response, ResponseAdmin)


class AggregateAnswerAdmin(admin.ModelAdmin):
    model = AggregateAnswer
    readonly_fields = ('question', 'project', 'value', 'options', 'list', 'response_count')
    list_display = ('survey_question', 'project', 'response_count', 'value', 'options', 'list')

    def survey_question(self, obj):
        return u"{0} : {1}".format(obj.question.survey, obj.question.display_title[:60])

admin.site.register(AggregateAnswer, AggregateAnswerAdmin)
