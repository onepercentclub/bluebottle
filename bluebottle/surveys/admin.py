from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from bluebottle.utils.widgets import SecureAdminURLFieldWidget

from bluebottle.surveys.models import Survey, Question, Response, Answer, AggregateAnswer


class QuestionAdminInline(admin.StackedInline):

    model = Question
    readonly_fields = ('type', )
    fields = readonly_fields + ('display', 'display_title',
                                'display_style', 'display_theme',
                                'left_label', 'right_label',
                                'aggregation')

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
    fields = ('remote_id', 'last_synced', 'active') + readonly_fields
    list_display = ('title', 'last_synced', 'response_count')

    inlines = [QuestionAdminInline]

    actions = ['synchronize_surveys']

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def response_count(self, obj):
        return obj.response_set.count()

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

    readonly_fields = ('remote_id', 'survey', 'user_type')
    list_display = ('survey', 'user_type', 'submitted', 'project', 'task', 'answer_count')

    search_fields = ('project__title', 'task__title')
    list_filter = ('user_type', )

    def answer_count(self, obj):
        return obj.answer_set.count()


admin.site.register(Response, ResponseAdmin)


class AggregateAnswerAdmin(admin.ModelAdmin):
    model = AggregateAnswer
    search_fields = ('project__title', 'question__title')
    readonly_fields = ('question', 'project', 'task', 'aggregation_type', 'value', 'options', 'list', 'response_count')
    list_display = ('survey_question', 'project', 'response_count', 'aggregation_type', 'value', 'options', 'list')
    list_filter = ('aggregation_type', 'question')

    def survey_question(self, obj):
        return format_html(
            u"<span title='{}'>{}</span>",
            unicode(obj.question)[:30], obj.question
        )


admin.site.register(AggregateAnswer, AggregateAnswerAdmin)
