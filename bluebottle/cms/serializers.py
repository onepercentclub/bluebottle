from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivityListSerializer
from bluebottle.tasks.serializers import TaskPreviewSerializer
from django.db import connection
from django.db.models import Sum

from fluent_contents.plugins.rawhtml.models import RawHtmlItem
from fluent_contents.plugins.text.models import TextItem
from fluent_contents.plugins.oembeditem.models import OEmbedItem

from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer, SorlImageField
)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.members.models import Member
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page, DocumentItem, ImageTextItem
from bluebottle.projects.models import Project
from bluebottle.statistics.statistics import Statistics

from rest_framework import serializers

from bluebottle.categories.serializers import CategorySerializer
from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage, HomePage, QuotesContent, SurveyContent, Quote,
    ProjectImagesContent, ProjectsContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent, TasksContent, CategoriesContent, StepsContent, LocationsContent,
    SlidesContent, Step, Logo, LogosContent, ContentLink, LinksContent,
    SitePlatformSettings, WelcomeContent,
    ActivitiesContent)
from bluebottle.geo.serializers import LocationSerializer
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.slides.models import Slide
from bluebottle.surveys.serializers import QuestionSerializer
from bluebottle.utils.fields import SafeField


class ItemSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return self.item_type


class RawHtmlItemSerializer(ItemSerializer):
    html = serializers.CharField()
    item_type = 'raw-html'

    class Meta:
        model = RawHtmlItem
        fields = ('id', 'html', 'type', )


class DocumentItemSerializer(ItemSerializer):
    item_type = 'document'

    class Meta:
        model = DocumentItem
        fields = ('id', 'text', 'document', 'type', )


class ImageTextItemSerializer(ItemSerializer):
    image = ImageSerializer()
    item_type = 'image-text'

    class Meta:
        model = ImageTextItem
        fields = ('id', 'text', 'image', 'ratio', 'align', 'type', )


class PictureItemSerializer(ItemSerializer):
    image = ImageSerializer()
    item_type = 'image'

    class Meta:
        model = PictureItem
        fields = ('id', 'align', 'image', 'type', )


class OEmbedItemSerializer(ItemSerializer):
    item_type = 'embed'

    class Meta:
        model = OEmbedItem
        fields = ('id', 'title', 'width', 'height', 'html', 'type', )


class TextItemSerializer(ItemSerializer):
    item_type = 'text'

    class Meta:
        model = TextItem
        fields = ('id', 'text', 'type', )


class MediaFileContentSerializer(serializers.Serializer):
    url = serializers.CharField(source='mediafile.file.url')
    caption = serializers.CharField(source='mediafile.translation.caption')

    def get_url(self, obj):
        return obj.file.url

    class Meta:
        fields = ('id', 'url', 'type')


class StatSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        if obj.value:
            return obj.value

        statistics = Statistics(
            start=self.context.get('start_date'),
            end=self.context.get('end_date'),
        )

        value = getattr(statistics, obj.type, 0)
        try:
            return {
                'amount': value.amount,
                'currency': str(value.currency)
            }
        except AttributeError:
            return value

    class Meta:
        model = Stat
        fields = ('id', 'title', 'type', 'value')


class StatsContentSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True)
    title = serializers.CharField()
    sub_title = serializers.CharField()

    class Meta:
        model = StatsContent
        fields = ('id', 'type', 'stats', 'title', 'sub_title')


class QuoteSerializer(serializers.ModelSerializer):
    image = SorlImageField('100x100', crop='center')

    class Meta:
        model = Quote
        fields = ('id', 'name', 'quote', 'image')


class QuotesContentSerializer(serializers.ModelSerializer):
    quotes = QuoteSerializer(many=True)

    class Meta:
        model = QuotesContent
        fields = ('id', 'quotes', 'type', 'title', 'sub_title')


class SurveyContentSerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, source='survey.visible_questions')
    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj):
        return obj.survey.response_set.count()

    class Meta:
        model = SurveyContent
        fields = ('id', 'type', 'response_count', 'answers', 'title', 'sub_title')


class ProjectImageSerializer(serializers.ModelSerializer):
    photo = ImageSerializer(source='image')

    class Meta:
        model = Project
        fields = ('id', 'photo', 'title', 'slug')


class ProjectImagesContentSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        projects = Project.objects.filter(
            status__slug__in=['done-complete', 'done-incomplete']
        ).order_by('?')

        if 'start_date' in self.context:
            projects = projects.filter(
                campaign_ended__gte=self.context['start_date']
            )

        if 'end_date' in self.context:
            projects = projects.filter(
                campaign_ended__lte=self.context['end_date']
            )

            return ProjectImageSerializer(projects, many=True).to_representation(projects[:8])

    class Meta:
        model = ProjectImagesContent
        fields = ('id', 'type', 'images', 'title', 'sub_title', 'description',
                  'action_text', 'action_link')


class ProjectsMapContentSerializer(serializers.ModelSerializer):
    def __repr__(self):
        if 'start_date' in self.context and 'end_date'in self.context:
            start = self.context['start_date'].strftime('%s') if self.context['start_date'] else 'none'
            end = self.context['end_date'].strftime('%s') if self.context['end_date'] else 'none'
            return 'MapsContent({},{})'.format(start, end)
        return 'MapsContent'

    class Meta:
        model = ProjectImagesContent
        fields = ('id', 'type', 'title', 'sub_title')


class ProjectsContentSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()

    def get_projects(self, obj):
        if obj.from_homepage:
            projects = Project.objects.filter(
                is_campaign=True, status__viewable=True
            ).order_by('?')[0:4]
        else:
            projects = obj.projects

        return ProjectPreviewSerializer(
            projects, many=True, context=self.context
        ).to_representation(projects)

    class Meta:
        model = ProjectsContent
        fields = ('id', 'type', 'title', 'sub_title', 'projects',
                  'action_text', 'action_link')


class ActivitiesContentSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()

    def get_activities(self, obj):
        if obj.highlighted:
            activities = Activity.objects.filter(
                highlight=True
            ).order_by('?')[0:4]
        else:
            activities = obj.activities

        return ActivityListSerializer(
            activities, many=True, context=self.context
        ).to_representation(activities)

    class Meta:
        model = ActivitiesContent
        fields = ('id', 'type', 'title', 'sub_title', 'activities',
                  'action_text', 'action_link')


class TasksContentSerializer(serializers.ModelSerializer):
    tasks = TaskPreviewSerializer(many=True)

    class Meta:
        model = TasksContent
        fields = ('id', 'type', 'title', 'sub_title', 'tasks',
                  'action_text', 'action_link')


class SlideSerializer(serializers.ModelSerializer):
    image = SorlImageField('1600x674', crop='center')
    background_image = SorlImageField('1600x674', crop='center')

    class Meta:
        model = Slide
        fields = (
            'background_image',
            'body',
            'id',
            'image',
            'link_text',
            'link_url',
            'tab_text',
            'title',
            'video_url',
        )


class SlidesContentSerializer(serializers.ModelSerializer):
    slides = serializers.SerializerMethodField()

    def get_slides(self, instance):
        slides = Slide.objects.published().filter(
            language=instance.language_code
        )

        return SlideSerializer(
            slides, many=True, context=self.context
        ).to_representation(slides)

    class Meta:
        model = SlidesContent
        fields = ('id', 'type', 'slides', 'title', 'sub_title',)


class CategoriesContentSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = CategoriesContent
        fields = ('id', 'type', 'title', 'sub_title', 'categories',)


class StepSerializer(serializers.ModelSerializer):
    image = SorlImageField('200x200', crop='center')
    text = SafeField(required=False, allow_blank=True)

    class Meta:
        model = Step
        fields = ('id', 'image', 'header', 'text', )


class StepsContentSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True)

    class Meta:
        model = StepsContent
        fields = ('id', 'type', 'title', 'sub_title', 'steps', 'action_text', 'action_link')


class LogoSerializer(serializers.ModelSerializer):
    image = SorlImageField('x150', crop='center')

    class Meta:
        model = Logo
        fields = ('id', 'image', 'link')


class LogosContentSerializer(serializers.ModelSerializer):
    logos = LogoSerializer(many=True)

    class Meta:
        model = LogosContent
        fields = ('id', 'type', 'title', 'sub_title', 'logos', 'action_text', 'action_link')


class LinkSerializer(serializers.ModelSerializer):
    image = SorlImageField('800x600', crop='center')

    class Meta:
        model = ContentLink
        fields = ('id', 'image', 'action_link', 'action_text', )


class LinksContentSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True)

    class Meta:
        model = LinksContent
        fields = ('id', 'type', 'title', 'sub_title', 'links', )


class WelcomeContentSerializer(serializers.ModelSerializer):
    greeting = serializers.SerializerMethodField()

    def get_greeting(self, instance):
        return instance.greetings.order_by('?')[0].text

    class Meta:
        model = WelcomeContent
        fields = ('id', 'type', 'preamble', 'greeting')


class LocationsContentSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True)

    class Meta:
        model = LocationsContent
        fields = ('id', 'type', 'title', 'sub_title', 'locations',)


class ShareResultsContentSerializer(serializers.ModelSerializer):
    statistics = serializers.SerializerMethodField()

    def get_statistics(self, instance):
        stats = Statistics(
            start=self.context.get('start_date'),
            end=self.context.get('end_date')
        )

        return {
            'people': stats.people_involved,
            'amount': {
                'amount': stats.donated_total.amount,
                'currency': str(stats.donated_total.currency)
            },
            'hours': stats.time_spent,
            'fundings': stats.fundings_succeeded,
            'assignments': stats.assignments_succeeded,
            'events': stats.events_succeeded,
            'votes': stats.votes_cast,
        }

    class Meta:
        model = ShareResultsContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'statistics', 'share_title', 'share_text')


class CoFinancerSerializer(serializers.Serializer):
    total = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = Member.objects.get(pk=obj['pk'])
        return UserPreviewSerializer(
            user, context=self.context
        ).to_representation(user)

    def get_id(self, obj):
        return obj['pk']

    def get_total(self, obj):
        return {
            'amount': obj['total'],
            'currency': obj['contribution__donation__amount_currency']
        }

    class Meta:
        fields = ('id', 'user', 'total')


class SupporterTotalContentSerializer(serializers.ModelSerializer):
    supporters = serializers.SerializerMethodField()
    co_financers = serializers.SerializerMethodField()

    def get_supporters(self, instance):
        stats = Statistics(
            start=self.context.get('start_date'),
            end=self.context.get('end_date')
        )
        return stats.people_involved

    def get_co_financers(self, instance):
        filters = {'is_co_financer': True}

        if 'start_date' in self.context:
            filters['contribution__transition_date__gte'] = self.context['start_date']

        if 'end_date' in self.context:
            filters['contribution__transition_date__lte'] = self.context['end_date']

        totals = Member.objects.filter(**filters)

        totals = totals.values(
            'pk', 'contribution__donation__amount_currency'
        ).annotate(
            total=Sum('contribution__donation__amount', distinct=True)
        )

        return CoFinancerSerializer(
            totals, many=True, context=self.context
        ).to_representation(totals)

    class Meta:
        model = SupporterTotalContent
        fields = ('id', 'type',
                  'title', 'sub_title', 'co_financer_title',
                  'supporters', 'co_financers')


class DefaultBlockSerializer(serializers.Serializer):
    def to_representation(self, obj):
        return {
            'type': obj.__class__._meta.model_name,
            'content': str(obj)
        }


class BlockSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj, StatsContent):
            serializer = StatsContentSerializer
        elif isinstance(obj, QuotesContent):
            serializer = QuotesContentSerializer
        elif isinstance(obj, ProjectImagesContent):
            serializer = ProjectImagesContentSerializer
        elif isinstance(obj, SurveyContent):
            serializer = SurveyContentSerializer
        elif isinstance(obj, ProjectsContent):
            serializer = ProjectsContentSerializer
        elif isinstance(obj, ShareResultsContent):
            serializer = ShareResultsContentSerializer
        elif isinstance(obj, ProjectsMapContent):
            serializer = ProjectsMapContentSerializer
        elif isinstance(obj, SupporterTotalContent):
            serializer = SupporterTotalContentSerializer
        elif isinstance(obj, TasksContent):
            serializer = TasksContentSerializer
        elif isinstance(obj, CategoriesContent):
            serializer = CategoriesContentSerializer
        elif isinstance(obj, SlidesContent):
            serializer = SlidesContentSerializer
        elif isinstance(obj, StepsContent):
            serializer = StepsContentSerializer
        elif isinstance(obj, LocationsContent):
            serializer = LocationsContentSerializer
        elif isinstance(obj, LogosContent):
            serializer = LogosContentSerializer
        elif isinstance(obj, LinksContent):
            serializer = LinksContentSerializer
        elif isinstance(obj, WelcomeContent):
            serializer = WelcomeContentSerializer
        elif isinstance(obj, RawHtmlItem):
            serializer = RawHtmlItemSerializer
        elif isinstance(obj, TextItem):
            serializer = TextItemSerializer
        elif isinstance(obj, OEmbedItem):
            serializer = OEmbedItemSerializer
        elif isinstance(obj, DocumentItem):
            serializer = DocumentItemSerializer
        elif isinstance(obj, PictureItem):
            serializer = PictureItemSerializer
        elif isinstance(obj, ImageTextItem):
            serializer = ImageTextItemSerializer
        elif isinstance(obj, ActivitiesContent):
            serializer = ActivitiesContentSerializer
        else:
            serializer = DefaultBlockSerializer

        return serializer(obj, context=self.context).to_representation(obj)


def watermark():
    return '{}/logo-overlay.png'.format(connection.tenant.client_name)


class ResultPageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(source='content.contentitems.all.translated', many=True)
    image = ImageSerializer()
    share_image = SorlImageField(
        '1200x600', source='image', crop='center',
        watermark=watermark,
        watermark_pos='center', watermark_size='1200x600'
    )

    class Meta:
        model = ResultPage
        fields = ('id', 'title', 'slug', 'start_date', 'image', 'share_image',
                  'end_date', 'description', 'blocks')


class HomePageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(source='content.contentitems.all.translated', many=True)

    class Meta:
        model = HomePage
        fields = ('id', 'blocks')


class PageSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    blocks = BlockSerializer(source='body.contentitems.all', many=True)

    class Meta:
        model = Page
        fields = ('title', 'id', 'blocks', 'language', 'full_page')


class NewsItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    blocks = BlockSerializer(source='contents.contentitems.all', many=True)
    main_image = SorlImageField('800x400')
    author = UserPreviewSerializer()

    class Meta:
        model = NewsItem
        fields = ('id', 'title', 'blocks', 'main_image', 'author',
                  'publication_date', 'allow_comments', 'language',
                  'main_image')


class FaviconsSerializer(serializers.Serializer):
    large = SorlImageField('194x194', source='*')
    small = SorlImageField('32x32', source='*')


class SitePlatformSettingsSerializer(serializers.ModelSerializer):
    favicons = FaviconsSerializer(source='favicon')

    class Meta:
        model = SitePlatformSettings
        fields = (
            'contact_email',
            'contact_phone',
            'copyright',
            'powered_by_link',
            'powered_by_logo',
            'powered_by_text',
            'logo',
            'favicons'
        )
