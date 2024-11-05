from builtins import object

from django.db.models import Q
from django.urls import reverse
from django_tools.middlewares.ThreadLocal import get_current_user
from fluent_contents.models import ContentItem
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
from bluebottle.cms.models import (
    HomePage, QuotesContent, Quote,
    ProjectsMapContent, CategoriesContent, StepsContent,
    SlidesContent, Step, Logo, LogosContent, ContentLink, LinksContent,
    SitePlatformSettings, HomepageStatisticsContent,
    ActivitiesContent, PlainTextItem, ImagePlainTextItem, ImageItem, DonateButtonContent
)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.members.models import Member
from bluebottle.pages.models import Page, DocumentItem, ImageTextItem, ActionItem, ColumnsItem, ImageTextRoundItem
from bluebottle.slides.models import Slide
from bluebottle.utils.fields import PolymorphicSerializerMethodResourceRelatedField, SafeField


class QuoteSerializer(serializers.ModelSerializer):
    image = SorlImageField('100x100', crop='center')

    class Meta(object):
        model = Quote
        fields = ('id', 'name', 'role', 'quote', 'image')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/quotes/quotes'


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


class StepSerializer(serializers.ModelSerializer):
    image = SorlImageField("500x500", upscale=False)

    text = SafeField(required=False, allow_blank=True)

    class Meta(object):
        model = Step
        fields = ('id', 'image', 'header', 'text', 'link', 'link_text', 'external')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/steps/steps'


class LogoSerializer(serializers.ModelSerializer):
    image = SorlImageField('x150', crop='center')

    class Meta(object):
        model = Logo
        fields = ('id', 'image', 'link', 'open_in_new_tab')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/logos/logos'


class LinkSerializer(serializers.ModelSerializer):
    image = SorlImageField('800x600', crop='center')

    class Meta(object):
        model = ContentLink
        fields = ('id', 'image', 'action_link', 'action_text', 'open_in_new_tab')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/links/links'


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
        fields = BaseBlockSerializer.Meta.fields + ('links',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/links'

    included_serializers = {
        'links': 'bluebottle.cms.serializers.LinkSerializer',
    }


class ProjectsMapBlockSerializer(BaseBlockSerializer):

    subregion = serializers.SerializerMethodField()

    def get_subregion(self, obj):
        if obj.map_type == 'office_subregion':
            user = get_current_user()
            if user and not user.is_anonymous and user.location and user.location.subregion:
                return user.location.subregion.name

    activities = CustomHyperlinkRelatedSerializer(
        link="/api/activities/locations"
    )

    activities_url = serializers.SerializerMethodField()

    def get_activities_url(self, obj):
        url = reverse('activity-location-list')
        if obj.map_type == 'office_subregion':
            user = get_current_user()
            if user and user.location and user.location.subregion:
                url += f'?office_location__subregion={user.location.subregion.pk}'
        return url

    class Meta(object):
        model = ProjectsMapContent
        fields = BaseBlockSerializer.Meta.fields + (
            'activities', 'activities_url', 'map_type', 'activities_url', 'subregion'
        )

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
            link += '&filter[highlight]=1'
        elif activity_type == 'matching':
            link += '&filter[matching]=1'
        elif activity_type == 'deed':
            link += '&filter[activity-type]=deed&filter[status]=open'
        elif activity_type == 'funding':
            link += '&filter[activity-type]=funding&filter[status]=open'
        elif activity_type == 'collect':
            link += '&filter[activity-type]=collect&filter[status]=open'
        elif activity_type == 'time_based':
            link += '&filter[activity-type]=time&filter[status]=open'
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


class DonateButtonBlockSerializer(BaseBlockSerializer):

    funding = ResourceRelatedField(
        read_only=True
    )

    class Meta(object):
        model = DonateButtonContent
        fields = ('id', 'type', 'title', 'sub_title', 'button_text', 'funding')
        included_resources = ['funding']

    class JSONAPIMeta:
        resource_name = 'pages/blocks/donate'

    included_serializers = {
        'funding': 'bluebottle.funding.serializers.FundingSerializer',
    }


class SlidesBlockSerializer(BaseBlockSerializer):
    slides = SerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        model=Slide
    )

    def get_slides(self, obj):
        user = get_current_user()
        if user and isinstance(user, Member) and user.location and user.location.subregion:
            return Slide.objects.published().filter(
                language=obj.language_code
            ).filter(Q(sub_region__isnull=True) | Q(sub_region=user.location.subregion))
        else:
            return Slide.objects.published().filter(
                language=obj.language_code
            ).filter(Q(sub_region__isnull=True))

    class Meta(object):
        model = SlidesContent
        fields = BaseBlockSerializer.Meta.fields + ('slides',)

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

        url = url + '?'

        if obj.stat_type == 'office_subregion':
            user = get_current_user()
            if user and user.location and user.location.subregion:
                url += f'office_location__subregion={user.location.subregion.pk}'

        if obj.year:
            url += f'&year={obj.year}'
        return {
            'related': url
        }


class StatsBlockSerializer(BaseBlockSerializer):
    title = serializers.CharField()
    sub_title = serializers.CharField()
    year = serializers.IntegerField()
    stats = StatsLinkSerializer()
    subregion = serializers.SerializerMethodField()

    def get_subregion(self, obj):
        if obj.stat_type == 'office_subregion':
            user = get_current_user()
            if user and not user.is_anonymous and user.location and user.location.subregion:
                return user.location.subregion.name

    class Meta(object):
        model = HomepageStatisticsContent
        fields = ('id', 'type', 'title', 'sub_title', 'year', 'stats', 'stat_type', 'subregion')

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


class PlainTextBlockSerializer(BaseBlockSerializer):
    text = SafeField()

    class Meta(object):
        model = PlainTextItem
        fields = ('id', 'text', 'type', 'title', 'sub_title',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/plain-text'


class ImagePlainTextBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()
    text = SafeField()

    class Meta(object):
        model = ImagePlainTextItem
        fields = (
            'id', 'text', 'image', 'video_url', 'ratio', 'align', 'type', 'title', 'sub_title',
            'action_text', 'action_link'
        )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/plain-text-image'


class ImageBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()

    class Meta(object):
        model = ImageItem
        fields = ('id', 'type', 'video_url', 'image', 'title', 'sub_title')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/image'


class PictureBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()

    class Meta(object):
        model = PictureItem
        fields = ('id', 'align', 'image', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/picture'


class TextBlockSerializer(BaseBlockSerializer):
    class Meta(object):
        model = TextItem
        fields = ('id', 'text', 'type', )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/text'

        fields = ('id', 'align', 'image', 'type',)


class ImageTextBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()

    class Meta(object):
        model = ImageTextItem

        fields = ('id', 'text', 'image', 'ratio', 'align', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/image-text'


class ImageRoundTextBlockSerializer(BaseBlockSerializer):
    image = ImageSerializer()

    class Meta(object):
        model = ImageTextRoundItem

        fields = ('id', 'text', 'image', 'align', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/image-rounded-text'


class DocumentBlockSerializer(BaseBlockSerializer):
    class Meta(object):
        model = DocumentItem

        fields = ('id', 'type', 'text', 'document',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/document'


class ActionBlockSerializer(BaseBlockSerializer):
    class Meta(object):
        model = ActionItem

        fields = ('id', 'type', 'link', 'title',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/action'


class RawHHTMLBlockSerializer(BaseBlockSerializer):
    class Meta(object):
        model = RawHtmlItem

        fields = ('id', 'type', 'html',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/raw-html'


class ColumnBlockSerializer(BaseBlockSerializer):

    class Meta(object):
        model = ColumnsItem

        fields = ('id', 'text1', 'text2', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/columns'


class FallbackBlockSerializer(serializers.Serializer):
    def to_representation(self, instance):
        print(instance.__class__)
        return {'id': instance.pk, 'type': self.JSONAPIMeta.resource_name}

    class Meta(object):
        model = None
        fields = ('id', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/unknown'


class OEmbedBlockSerializer(BaseBlockSerializer):
    item_type = 'embed'

    class Meta(object):
        model = OEmbedItem
        fields = ('id', 'title', 'width', 'height', 'html', 'type',)

    class JSONAPIMeta:
        resource_name = 'pages/blocks/oembed'


class BlockSerializer(PolymorphicModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._poly_force_type_resolution = False

    polymorphic_serializers = [
        SlidesBlockSerializer,
        StepsBlockSerializer,
        ActivitiesBlockSerializer,
        DonateButtonBlockSerializer,
        ProjectsMapBlockSerializer,
        LinksBlockSerializer,
        StatsBlockSerializer,
        QuotesBlockSerializer,
        LogosBlockSerializer,
        CategoriesBlockSerializer,
        TextBlockSerializer,
        ImageTextBlockSerializer,
        ImageRoundTextBlockSerializer,
        ImageBlockSerializer,
        PictureBlockSerializer,
        ImagePlainTextBlockSerializer,
        ImageBlockSerializer,
        PlainTextBlockSerializer,
        TextBlockSerializer,
        ColumnBlockSerializer,
        OEmbedBlockSerializer,
        DocumentBlockSerializer,
        ActionBlockSerializer,
        RawHHTMLBlockSerializer
    ]

    def get_slides(self, obj):
        return Slide.objects.published().filter(
            language=obj.language_code
        )

    @classmethod
    def get_polymorphic_serializer_for_instance(cls, instance):
        try:
            return super().get_polymorphic_serializer_for_instance(instance)
        except NotImplementedError:
            return FallbackBlockSerializer

    class Meta:
        model = ContentItem

    class JSONAPIMeta:
        included_resources = [
            'links', 'steps', 'quotes', 'slides', 'logos', 'categories', 'funding',
            'full_page'

        ]

    included_serializers = {
        'steps': 'bluebottle.cms.serializers.StepSerializer',
        'links': 'bluebottle.cms.serializers.LinkSerializer',
        'slides': 'bluebottle.cms.serializers.SlideSerializer',
        'quotes': 'bluebottle.cms.serializers.QuoteSerializer',
        'funding': 'bluebottle.funding.serializers.FundingSerializer',

        'logos': 'bluebottle.cms.serializers.LogoSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
    }


class BaseCMSSerializer(ModelSerializer):
    blocks = PolymorphicSerializerMethodResourceRelatedField(
        BlockSerializer,
        read_only=True,
        many=True,
        model=ContentItem
    )

    content_attribute = 'content'

    def get_blocks(self, obj):
        return obj.content.contentitems.all().translated()

    class Meta(object):
        fields = ('id', 'blocks')

    class JSONAPIMeta(object):
        included_resources = [
            'blocks',
            'blocks.steps',
            'blocks.links',
            'blocks.slides',
            'blocks.quotes',
            'blocks.funding',
            'blocks.funding.image',
            'blocks.logos',
            'blocks.categories',
        ]

    included_serializers = {
        'blocks': 'bluebottle.cms.serializers.BlockSerializer',
        'steps': 'bluebottle.cms.serializers.StepSerializer',
        'links': 'bluebottle.cms.serializers.LinkSerializer',
        'slides': 'bluebottle.cms.serializers.SlideSerializer',
        'quotes': 'bluebottle.cms.serializers.QuoteSerializer',
        'funding': 'bluebottle.funding.serializers.FundingSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'logos': 'bluebottle.cms.serializers.LogoSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
    }


class HomeSerializer(BaseCMSSerializer):
    class Meta(BaseCMSSerializer.Meta):
        model = HomePage

    class JSONAPIMeta(BaseCMSSerializer.JSONAPIMeta):
        resource_name = 'homepages'


class PageSerializer(BaseCMSSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    def get_blocks(self, obj):
        return obj.content.contentitems.all()

    class Meta(BaseCMSSerializer.Meta):
        model = Page
        fields = BaseCMSSerializer.Meta.fields + ('title', 'show_title', 'full_page', 'slug')

    class JSONAPIMeta(BaseCMSSerializer.JSONAPIMeta):
        resource_name = 'pages'


class NewsItemSerializer(BaseCMSSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    main_image = SorlImageField('800x400')

    content_attribute = 'contents'

    def get_blocks(self, obj):
        return obj.contents.contentitems.all()

    class Meta(BaseCMSSerializer.Meta):
        model = Page
        fields = BaseCMSSerializer.Meta.fields + (
            'title', 'author', 'publication_date', 'slug', 'main_image'
        )

    class JSONAPIMeta(BaseCMSSerializer.JSONAPIMeta):
        resource_name = 'news-item'
        included_resources = BaseCMSSerializer.JSONAPIMeta.included_resources + ['author', ]

    included_serializers = dict(
        author='bluebottle.initiatives.serializers.MemberSerializer',
        **BaseCMSSerializer.included_serializers
    )


class NewsItemPreviewSerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    class Meta:
        model = Page
        fields = ('id', 'title', 'slug', 'publication_date',)

    class JSONAPIMeta:
        resource_name = 'news-item-preview'


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
            'footer_banner',
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
