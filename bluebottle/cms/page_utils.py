import os

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.http import Http404
from fluent_contents.models import ContentItem, Placeholder
from fluent_contents.plugins.text.models import TextItem

from bluebottle.clients import properties
from bluebottle.contentplugins.models import PictureItem
from bluebottle.pages.models import ImageTextItem, Page
from bluebottle.utils.utils import get_language_from_request


EDITABLE_BLOCK_MODELS = (
    'TextItem',
    'PictureItem',
    'ImageTextItem',
)

BLOCK_RESOURCE_TYPES = {
    'pages/blocks/text': TextItem,
    'pages/blocks/picture': PictureItem,
    'pages/blocks/image-text': ImageTextItem,
}

BLOCK_CREATE_DEFAULTS = {
    'pages/blocks/text': {'text': ''},
    'pages/blocks/picture': {'align': 'center'},
    'pages/blocks/image-text': {'text': '', 'align': 'left', 'ratio': 6},
}


def get_page_for_block(block):
    placeholder_id = getattr(block, 'placeholder_id', None)
    if not placeholder_id:
        return None

    try:
        placeholder = Placeholder.objects.get(pk=placeholder_id)
    except Placeholder.DoesNotExist:
        return None

    if placeholder.parent_type_id != ContentType.objects.get_for_model(Page).pk:
        return None

    return Page.objects.filter(pk=placeholder.parent_id).first()


def is_editable_page_block(block):
    return block.__class__.__name__ in EDITABLE_BLOCK_MODELS and get_page_for_block(block) is not None


def resolve_page(slug, request):
    if (
        request.user.is_authenticated and
        request.user.has_perm('pages.api_change_page')
    ):
        queryset = Page.objects.all()
    else:
        queryset = Page.objects.published()

    language = get_language_from_request(request)
    try:
        return queryset.get(language=language, slug=slug)
    except ObjectDoesNotExist:
        try:
            return queryset.get(language=properties.LANGUAGE_CODE, slug=slug)
        except ObjectDoesNotExist:
            page = queryset.filter(slug=slug).first()
            if page:
                return page
            raise Http404


def get_or_create_page_placeholder(page):
    placeholder = Placeholder.objects.filter(
        parent_type=ContentType.objects.get_for_model(Page),
        parent_id=page.pk,
        slot='blog_contents',
    ).first()
    if placeholder:
        return placeholder
    return Placeholder.objects.create_for_object(page, slot='blog_contents')


def get_next_block_sort_order(placeholder):
    last = placeholder.contentitems.all().order_by('-sort_order').first()
    if last:
        return last.sort_order + 1
    return 1


def create_page_block(page, resource_type, validated_data, write_serializer_class):
    model_class = BLOCK_RESOURCE_TYPES[resource_type]
    placeholder = get_or_create_page_placeholder(page)
    sort_order = get_next_block_sort_order(placeholder)
    defaults = BLOCK_CREATE_DEFAULTS.get(resource_type, {})

    instance = model_class.objects.create_for_placeholder(
        placeholder,
        sort_order=sort_order,
        **defaults
    )

    write_serializer = write_serializer_class()
    write_serializer.update(instance, validated_data)
    return ContentItem.objects.get(pk=instance.pk).get_real_instance()


def apply_uploaded_image(block, field_name, uploaded_image):
    if not uploaded_image or not uploaded_image.file:
        return

    field_file = getattr(block, field_name)
    filename = os.path.basename(uploaded_image.file.name)
    uploaded_image.file.open('rb')
    try:
        field_file.save(filename, ContentFile(uploaded_image.file.read()), save=False)
    finally:
        uploaded_image.file.close()
