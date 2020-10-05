from builtins import str
from builtins import object
from django.db.models import Sum
from fluent_contents.plugins.oembeditem.models import OEmbedItem
from fluent_contents.plugins.rawhtml.models import RawHtmlItem
from fluent_contents.plugins.text.models import TextItem
from rest_framework import serializers

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivityListSerializer
from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer, SorlImageField
)
from bluebottle.categories.serializers import CategorySerializer
from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage, HomePage, QuotesContent, Quote,
    ShareResultsContent, ProjectsMapContent, SupporterTotalContent, CategoriesContent, StepsContent, LocationsContent,
    SlidesContent, Step, Logo, LogosContent, ContentLink, LinksContent,
    SitePlatformSettings, WelcomeContent, HomepageStatisticsContent,
    ActivitiesContent)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.geo.serializers import LocationSerializer
from bluebottle.members.models import Member
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page, DocumentItem, ImageTextItem, ActionItem, ColumnsItem, ImageTextRoundItem
from bluebottle.slides.models import Slide
from bluebottle.statistics.models import BaseStatistic
from bluebottle.statistics.statistics import Statistics
from bluebottle.utils.fields import SafeField


class ItemSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return self.item_type


class RawHtmlItemSerializer(ItemSerializer):
    html = SafeField()
    item_type = 'raw-html'

    class Meta(object):
        model = RawHtmlItem
        fields = ('id', 'html', 'type', )


class DocumentItemSerializer(ItemSerializer):
    item_type = 'document'

    class Meta(object):
        model = DocumentItem
        fields = ('id', 'text', 'document', 'type', )


class ImageTextItemSerializer(ItemSerializer):
    image = ImageSerializer()
    item_type = 'image-text'

    class Meta(object):
        model = ImageTextItem
        fields = ('id', 'text', 'image', 'ratio', 'align', 'type', )


class ImageTextRoundItemSerializer(ItemSerializer):
    image = ImageSerializer()
    item_type = 'image-text-round'

    class Meta(object):
        model = ImageTextItem
        fields = ('id', 'text', 'image', 'type', )


class PictureItemSerializer(ItemSerializer):
    image = ImageSerializer()
    item_type = 'image'

    class Meta(object):
        model = PictureItem
        fields = ('id', 'align', 'image', 'type', )


class OEmbedItemSerializer(ItemSerializer):
    item_type = 'embed'

    class Meta(object):
        model = OEmbedItem
        fields = ('id', 'title', 'width', 'height', 'html', 'type', )


class TextItemSerializer(ItemSerializer):
    item_type = 'text'

    class Meta(object):
        model = TextItem
        fields = ('id', 'text', 'type', )


class MediaFileContentSerializer(serializers.Serializer):
    url = serializers.CharField(source='mediafile.file.url')
    caption = serializers.CharField(source='mediafile.translation.caption')

    def get_url(self, obj):
        return obj.file.url

    class Meta(object):
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

    class Meta(object):
        model = Stat
        fields = ('id', 'title', 'type', 'value')


class StatsContentSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True)
    title = serializers.CharField()
    sub_title = serializers.CharField()

    class Meta(object):
        model = StatsContent
        fields = ('id', 'type', 'stats', 'title', 'sub_title', )


class HomepageStatisticsContentSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    sub_title = serializers.CharField()
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return len(BaseStatistic.objects.filter(active=True))

    class Meta(object):
        model = HomepageStatisticsContent
        fields = ('id', 'type', 'title', 'sub_title', 'count')


class QuoteSerializer(serializers.ModelSerializer):
    image = SorlImageField('100x100', crop='center')

    class Meta(object):
        model = Quote
        fields = ('id', 'name', 'quote', 'image')


class QuotesContentSerializer(serializers.ModelSerializer):
    quotes = QuoteSerializer(many=True)

    class Meta(object):
        model = QuotesContent
        fields = ('id', 'quotes', 'type', 'title', 'sub_title')


class ProjectsMapContentSerializer(serializers.ModelSerializer):
    def __repr__(self):
        if 'start_date' in self.context and 'end_date' in self.context:
            start = self.context['start_date'].strftime(
                '%s') if self.context['start_date'] else 'none'
            end = self.context['end_date'].strftime(
                '%s') if self.context['end_date'] else 'none'
            return 'MapsContent({},{})'.format(start, end)
        return 'MapsContent'

    class Meta(object):
        model = ProjectsMapContent
        fields = ('id', 'type', 'title', 'sub_title')


class ActivitiesContentSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()

    def get_activities(self, obj):
        if obj.highlighted:
            activities = Activity.objects.filter(
                highlight=True
            ).exclude(
                status__in=[
                    'draft', 'needs_work', 'submitted',
                    'deleted', 'closed', 'rejected'
                ]
            ).order_by('?')[0:4]
        else:
            activities = obj.activities

        return ActivityListSerializer(
            activities, many=True, context=self.context
        ).to_representation(activities)

    class Meta(object):
        model = ActivitiesContent
        fields = ('id', 'type', 'title', 'sub_title', 'activities',
                  'action_text', 'action_link')


class SlideSerializer(serializers.ModelSerializer):
    image = SorlImageField('1600x674', crop='center')
    background_image = SorlImageField('1600x674', crop='center')

    class Meta(object):
        model = Slide
        fields = (
            'background_image',
            'video',
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

    class Meta(object):
        model = SlidesContent
        fields = ('id', 'type', 'slides', 'title', 'sub_title',)


class CategoriesContentSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta(object):
        model = CategoriesContent
        fields = ('id', 'type', 'title', 'sub_title', 'categories',)


class StepSerializer(serializers.ModelSerializer):
    image = SorlImageField('200x200', crop='center')
    text = SafeField(required=False, allow_blank=True)

    class Meta(object):
        model = Step
        fields = ('id', 'image', 'header', 'text', )


class StepsContentSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True)

    class Meta(object):
        model = StepsContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'steps', 'action_text', 'action_link')


class LogoSerializer(serializers.ModelSerializer):
    image = SorlImageField('x150', crop='center')

    class Meta(object):
        model = Logo
        fields = ('id', 'image', 'link')


class LogosContentSerializer(serializers.ModelSerializer):
    logos = LogoSerializer(many=True)

    class Meta(object):
        model = LogosContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'logos', 'action_text', 'action_link')


class LinkSerializer(serializers.ModelSerializer):
    image = SorlImageField('800x600', crop='center')

    class Meta(object):
        model = ContentLink
        fields = ('id', 'image', 'action_link', 'action_text', )


class ActionSerializer(ItemSerializer):
    item_type = 'action'

    class Meta(object):
        model = ActionItem
        fields = ('id', 'type', 'link', 'title', )


class ColumnsSerializer(ItemSerializer):
    item_type = 'columns'

    class Meta(object):
        model = ColumnsItem
        fields = ('id', 'type', 'text1', 'text2', )


class LinksContentSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True)

    class Meta(object):
        model = LinksContent
        fields = ('id', 'type', 'title', 'sub_title', 'links', )


class WelcomeContentSerializer(serializers.ModelSerializer):
    greeting = serializers.SerializerMethodField()

    def get_greeting(self, instance):
        return instance.greetings.order_by('?')[0].text

    class Meta(object):
        model = WelcomeContent
        fields = ('id', 'type', 'preamble', 'greeting')


class LocationsContentSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True)

    class Meta(object):
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
            'fundraisers': stats.fundings_succeeded,
            'tasks': stats.assignments_succeeded,
            'events': stats.events_succeeded
        }

    class Meta(object):
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

    class Meta(object):
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

    class Meta(object):
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
        elif isinstance(obj, HomepageStatisticsContent):
            serializer = HomepageStatisticsContentSerializer
        elif isinstance(obj, QuotesContent):
            serializer = QuotesContentSerializer
        elif isinstance(obj, ShareResultsContent):
            serializer = ShareResultsContentSerializer
        elif isinstance(obj, ProjectsMapContent):
            serializer = ProjectsMapContentSerializer
        elif isinstance(obj, SupporterTotalContent):
            serializer = SupporterTotalContentSerializer
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
        elif isinstance(obj, ImageTextRoundItem):
            serializer = ImageTextRoundItemSerializer
        elif isinstance(obj, ActivitiesContent):
            serializer = ActivitiesContentSerializer
        elif isinstance(obj, ActionItem):
            serializer = ActionSerializer
        elif isinstance(obj, ColumnsItem):
            serializer = ColumnsSerializer
        else:
            serializer = DefaultBlockSerializer

        return serializer(obj, context=self.context).to_representation(obj)


class ResultPageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(
        source='content.contentitems.all.translated', many=True)
    image = ImageSerializer()
    share_image = SorlImageField(
        '1200x600', source='image', crop='center',
    )

    class Meta(object):
        model = ResultPage
        fields = ('id', 'title', 'slug', 'start_date', 'image', 'share_image',
                  'end_date', 'description', 'blocks')


class HomePageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(
        source='content.contentitems.all.translated', many=True)

    class Meta(object):
        model = HomePage
        fields = ('id', 'blocks')


class PageSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    blocks = BlockSerializer(source='body.contentitems.all', many=True)

    class Meta(object):
        model = Page
        fields = ('title', 'id', 'blocks', 'language', 'full_page')


class NewsItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    blocks = BlockSerializer(source='contents.contentitems.all', many=True)
    main_image = SorlImageField('800x400')
    author = UserPreviewSerializer()

    class Meta(object):
        model = NewsItem
        fields = ('id', 'title', 'blocks', 'main_image', 'author',
                  'publication_date', 'allow_comments', 'language',
                  'main_image')


class FaviconsSerializer(serializers.Serializer):
    large = SorlImageField('194x194', source='*')
    small = SorlImageField('32x32', source='*')


class SitePlatformSettingsSerializer(serializers.ModelSerializer):
    favicons = FaviconsSerializer(source='favicon')

    class Meta(object):
        model = SitePlatformSettings
        fields = (
            'contact_email',
            'contact_phone',
            'copyright',
            'powered_by_link',
            'powered_by_logo',
            'powered_by_text',
            'metadata_title',
            'metadata_description',
            'metadata_keywords',
            'start_page',
            'logo',
            'favicons'
        )
