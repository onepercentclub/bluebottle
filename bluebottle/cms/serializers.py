from builtins import object
from builtins import str

from django.db.models import Sum
from django.urls import reverse
from django.utils.html import strip_tags
from fluent_contents.models import ContentItem, Placeholder
from fluent_contents.plugins.oembeditem.models import OEmbedItem
from fluent_contents.plugins.rawhtml.models import RawHtmlItem
from fluent_contents.plugins.text.models import TextItem
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField, SerializerMethodResourceRelatedField, \
    HyperlinkedRelatedField
from rest_framework_json_api.serializers import ModelSerializer, PolymorphicModelSerializer

from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer, SorlImageField, CustomHyperlinkRelatedSerializer
)
from bluebottle.categories.serializers import CategorySerializer
from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage, HomePage, QuotesContent, Quote,
    ShareResultsContent, ProjectsMapContent, SupporterTotalContent, CategoriesContent, StepsContent, LocationsContent,
    SlidesContent, Step, Logo, LogosContent, ContentLink, LinksContent,
    SitePlatformSettings, WelcomeContent, HomepageStatisticsContent,
    ActivitiesContent, PlainTextItem, ImagePlainTextItem)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.geo.serializers import OfficeSerializer
from bluebottle.members.models import Member
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page, DocumentItem, ImageTextItem, ActionItem, ColumnsItem, ImageTextRoundItem
from bluebottle.slides.models import Slide
from bluebottle.statistics.models import BaseStatistic
from bluebottle.statistics.statistics import Statistics
from bluebottle.utils.fields import PolymorphicSerializerMethodResourceRelatedField, SafeField


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
    year = serializers.IntegerField()
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return len(BaseStatistic.objects.filter(active=True))

    class Meta(object):
        model = HomepageStatisticsContent
        fields = ('id', 'type', 'title', 'sub_title', 'year', 'count')


class QuoteSerializer(serializers.ModelSerializer):
    image = SorlImageField('100x100', crop='center')

    class Meta(object):
        model = Quote
        fields = ('id', 'name', 'quote', 'image')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/quotes/quotes'


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

    class Meta(object):
        model = ActivitiesContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'action_text', 'action_link')


class SlideSerializer(serializers.ModelSerializer):
    background_image = SorlImageField('1600x674', crop='center')
    small_background_image = SorlImageField('200x84', crop='center', source='background_image')

    class Meta(object):
        model = Slide
        fields = (
            'background_image',
            'small_background_image',
            'video',
            'body',
            'id',
            'link_text',
            'link_url',
            'tab_text',
            'title',
            'video_url',
        )


class OldSlidesContentSerializer(serializers.ModelSerializer):
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

    class JSONAPIMeta:
        resource_name = 'pages/blocks/categories/categories'


class StepSerializer(serializers.ModelSerializer):
    image = SorlImageField('200x200', crop='center')
    text = SafeField(required=False, allow_blank=True)

    class Meta(object):
        model = Step
        fields = ('id', 'image', 'header', 'text', 'link', 'external')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/steps/steps'


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
        fields = ('id', 'image', 'link', 'open_in_new_tab')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/logos/logos'


class LogosContentSerializer(serializers.ModelSerializer):
    logos = LogoSerializer(many=True)
    action_text = serializers.CharField(source='title')

    class Meta(object):
        model = LogosContent
        fields = ('id', 'type', 'action_text', 'sub_title',
                  'logos')


class LinkSerializer(serializers.ModelSerializer):
    image = SorlImageField('800x600', crop='center')

    class Meta(object):
        model = ContentLink
        fields = ('id', 'image', 'action_link', 'action_text', 'open_in_new_tab')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/links/links'


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
    locations = OfficeSerializer(many=True)

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
            'time': stats.time_activities_succeeded,
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
            'currency': obj['contributor__donor__amount_currency']
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
            filters['contributor__transition_date__gte'] = self.context['start_date']

        if 'end_date' in self.context:
            filters['contributor__transition_date__lte'] = self.context['end_date']

        totals = Member.objects.filter(**filters)

        totals = totals.values(
            'pk', 'contributor__donor__amount_currency'
        ).annotate(
            total=Sum('contributor__donor__amount')
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


class OldBlockSerializer(serializers.Serializer):
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
            serializer = OldSlidesContentSerializer
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
    blocks = OldBlockSerializer(
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
    blocks = OldBlockSerializer(
        source='content.contentitems.all.translated', many=True)

    class Meta(object):
        model = HomePage
        fields = ('id', 'blocks')


class BaseBlockSerializer(ModelSerializer):
    type = serializers.SerializerMethodField(read_only=True)

    class Meta(object):
        model = ContentItem
        fields = ('id', 'type', 'language_code', 'title', 'sub_title',)

    def get_type(self, obj):
        return self.JSONAPIMeta.resource_name

    class JSONAPIMeta:
        resource_name = 'pages/blocks/block'


class LinksBlockSerializer(BaseBlockSerializer):
    links = ResourceRelatedField(
        read_only=True,
        many=True,
    )

    class Meta(object):
        model = LinksContent
        includes_resources = ['links']
        fields = BaseBlockSerializer.Meta.fields + ('links', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/links'

    included_serializers = {
        'links': 'bluebottle.cms.serializers.LinkSerializer',
    }


class ProjectsMapBlockSerializer(BaseBlockSerializer):
    activities = CustomHyperlinkRelatedSerializer(
        link="/api/activities/locations"
    )

    class Meta(object):
        model = ProjectsMapContent
        fields = BaseBlockSerializer.Meta.fields + ('activities', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/map'


class ActivitySearchRelatedSerializer(HyperlinkedRelatedField):

    def __init__(self, **kwargs):
        super(HyperlinkedRelatedField, self).__init__(source='parent', read_only=True, **kwargs)

    def get_links(self, *args, **kwargs):
        link = reverse('activity-preview-list')
        link += '?page[size]=4'
        activity_type = self.root.data['activity_type']
        if activity_type == 'highlighted':
            link += '&filter[highlighted]=true'
        elif activity_type == 'matching':
            link += '&sort=popularity'
        elif activity_type == 'deed':
            link += '&filter[type]=deed'
        elif activity_type == 'funding':
            link += '&filter[type]=funding'
        elif activity_type == 'collecting':
            link += '&filter[type]=collect'
        elif activity_type == 'time_based':
            link += '&filter[type]=time_based'
        return {
            'related': link
        }


class ActivitiesBlockSerializer(BaseBlockSerializer):

    activities = ActivitySearchRelatedSerializer()

    def get_links(self, *args, **kwargs):
        link = reverse('activity-preview-list')
        link = "/api/activities/search?filter[highlight]=true&page[size]=4"
        return {
            'related': link
        }

    class Meta(object):
        model = ActivitiesContent
        fields = BaseBlockSerializer.Meta.fields + ('action_text', 'action_link', 'activities', 'activity_type')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/activities'


class SlidesBlockSerializer(BaseBlockSerializer):
    slides = SerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        model=Slide
    )

    def get_slides(self, obj):
        return Slide.objects.published().filter(
            language=obj.language_code
        )

    class Meta(object):
        model = SlidesContent
        fields = BaseBlockSerializer.Meta.fields + ('slides', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/slides'
        included_resources = ['slides']

    included_serializers = {
        'slides': 'bluebottle.cms.serializers.SlideSerializer',
    }


class StepsBlockSerializer(BaseBlockSerializer):
    steps = ResourceRelatedField(
        many=True,
        read_only=True
    )

    class Meta(object):
        model = StepsContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'steps', 'action_text', 'action_link')
        included_resources = ['steps']

    class JSONAPIMeta:
        resource_name = 'pages/blocks/steps'

    included_serializers = {
        'steps': 'bluebottle.cms.serializers.StepSerializer',
    }


class StatsLinkSerializer(CustomHyperlinkRelatedSerializer):

    def get_links(self, *args, **kwargs):
        url = reverse('statistics')
        obj = args[0]
        if obj.year:
            url += f'?year={obj.year}'
        return {
            'related': url
        }


class StatsBlockSerializer(BaseBlockSerializer):
    title = serializers.CharField()
    sub_title = serializers.CharField()
    year = serializers.IntegerField()
    stats = StatsLinkSerializer()

    class Meta(object):
        model = HomepageStatisticsContent
        fields = ('id', 'type', 'title', 'sub_title', 'year', 'stats')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/stats'


class QuotesBlockSerializer(BaseBlockSerializer):
    quotes = ResourceRelatedField(
        many=True,
        read_only=True,
    )

    class Meta(object):
        model = QuotesContent
        fields = ('id', 'quotes', 'type', 'title', 'sub_title', 'quotes')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/quotes'
        included_resources = [
            'quotes'
        ]


class CategoriesBlockSerializer(BaseBlockSerializer):
    categories = ResourceRelatedField(
        many=True,
        read_only=True,
    )

    class Meta(object):
        model = CategoriesContent
        fields = ('id', 'type', 'title', 'sub_title', 'categories')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/categories'
        included_resources = [
            'categories'
        ]

    included_serializers = {
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
    }


class LogosBlockSerializer(BaseBlockSerializer):
    logos = ResourceRelatedField(
        many=True,
        read_only=True,
    )

    class Meta(object):
        model = LogosContent
        fields = ('id', 'logos', 'type', 'title', 'sub_title')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/logos'
        included_resources = [
            'logos'
        ]


class TextBlockSerializer(BaseBlockSerializer):

    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return strip_tags(obj.text)

    class Meta(object):
        model = PlainTextItem
        fields = ('id', 'text', 'type', 'title', 'sub_title', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/plain-text'


class ImageTextBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return strip_tags(obj.text)

    class Meta(object):
        model = ImagePlainTextItem
        fields = ('id', 'text', 'image', 'ratio', 'align', 'type', 'title', 'sub_title', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/plain-text-image'


class BlockSerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        SlidesBlockSerializer,
        StepsBlockSerializer,
        ActivitiesBlockSerializer,
        ProjectsMapBlockSerializer,
        LinksBlockSerializer,
        StatsBlockSerializer,
        QuotesBlockSerializer,
        LogosBlockSerializer,
        CategoriesBlockSerializer,
        TextBlockSerializer,
        ImageTextBlockSerializer,
    ]

    def get_slides(self, obj):
        return Slide.objects.published().filter(
            language=obj.language_code
        )

    class Meta:
        model = ContentItem

    class JSONAPIMeta:
        included_resources = [
            'links', 'steps', 'quotes', 'slides', 'logos', 'categories'
        ]

    included_serializers = {
        'steps': 'bluebottle.cms.serializers.StepSerializer',
        'links': 'bluebottle.cms.serializers.LinkSerializer',
        'slides': 'bluebottle.cms.serializers.SlideSerializer',
        'quotes': 'bluebottle.cms.serializers.QuoteSerializer',
        'logos': 'bluebottle.cms.serializers.LogoSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
    }


class HomeSerializer(ModelSerializer):

    blocks = PolymorphicSerializerMethodResourceRelatedField(
        BlockSerializer,
        read_only=True,
        many=True,
        model=ContentItem
    )

    def get_blocks(self, obj):
        return obj.content.contentitems.all().translated()

    class Meta(object):
        model = Placeholder
        fields = ('id', 'blocks')

    class JSONAPIMeta(object):
        resource_name = 'pages'
        included_resources = [
            'blocks',
            'blocks.steps',
            'blocks.links',
            'blocks.slides',
            'blocks.quotes',
            'blocks.logos',
            'blocks.categories',
        ]

    included_serializers = {
        'blocks': 'bluebottle.cms.serializers.BlockSerializer',
        'steps': 'bluebottle.cms.serializers.StepSerializer',
        'links': 'bluebottle.cms.serializers.LinkSerializer',
        'slides': 'bluebottle.cms.serializers.SlideSerializer',
        'quotes': 'bluebottle.cms.serializers.QuoteSerializer',
        'logos': 'bluebottle.cms.serializers.LogoSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
    }


class OldPageSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    blocks = OldBlockSerializer(source='body.contentitems.all', many=True)

    class Meta(object):
        model = Page
        fields = ('title', 'id', 'blocks', 'language', 'full_page')


class PageSerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    blocks = OldBlockSerializer(source='body.contentitems.all', many=True)

    class Meta(object):
        model = Page
        fields = ('title', 'id', 'blocks', 'language', 'full_page')

    class JSONAPIMeta(object):
        resource_name = 'pages'


class NewsItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    blocks = OldBlockSerializer(source='contents.contentitems.all', many=True)
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
            'favicons',
            'action_color',
            'action_text_color',
            'alternative_link_color',
            'description_color',
            'description_text_color',
            'footer_color',
            'footer_text_color',
            'title_font',
            'body_font',
        )
