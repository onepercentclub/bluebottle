from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from bluebottle.clients import properties
from bluebottle.content.models import ContentBlock, ContentPage
from bluebottle.utils.utils import get_language_from_request


BLOCK_RESOURCE_TYPES = {
    'content/blocks/title': ContentBlock.BlockType.title,
    'content/blocks/text': ContentBlock.BlockType.text,
    'content/blocks/image': ContentBlock.BlockType.image,
    'content/blocks/text-image': ContentBlock.BlockType.text_image,
    'content/blocks/video': ContentBlock.BlockType.video,
    'content/blocks/button': ContentBlock.BlockType.button,
    'content/blocks/spacer': ContentBlock.BlockType.spacer,
}

BLOCK_TYPE_TO_RESOURCE = {value: key for key, value in BLOCK_RESOURCE_TYPES.items()}

BLOCK_CREATE_DEFAULTS = {
    ContentBlock.BlockType.title: {
        'title_text': '',
        'title_level': 1,
    },
    ContentBlock.BlockType.text: {
        'text': '',
    },
    ContentBlock.BlockType.image: {
        'align': ContentBlock.ImageAlign.center,
    },
    ContentBlock.BlockType.text_image: {
        'text': '',
        'align': ContentBlock.TextImageAlign.left,
        'ratio': 6,
    },
    ContentBlock.BlockType.video: {
        'video_url': '',
    },
    ContentBlock.BlockType.button: {
        'button_label': '',
        'button_url': '',
    },
    ContentBlock.BlockType.spacer: {
        'spacer_size': ContentBlock.SpacerSize.medium,
    },
}


def resolve_page(slug, request):
    if (
        request.user.is_authenticated and
        request.user.has_perm('pages.api_change_page')
    ):
        queryset = ContentPage.objects.all()
    else:
        queryset = ContentPage.objects.published()

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


def get_next_block_sort_order(page):
    last = page.blocks.order_by('-sort_order').first()
    if last:
        return last.sort_order + 1
    return 1


def resolve_insert_sort_order(page, insert_after=None, insert_before=None):
    if insert_after and insert_before:
        raise ValueError('Specify either insertAfter or insertBefore, not both')

    if not insert_after and not insert_before:
        return get_next_block_sort_order(page)

    items = list(page.blocks.order_by('sort_order', 'pk'))

    if insert_after:
        anchor_id = int(insert_after)
        if not any(item.pk == anchor_id for item in items):
            raise ValueError('Block not found on this page')
        insert_index = next(
            index for index, item in enumerate(items) if item.pk == anchor_id
        ) + 1
    else:
        anchor_id = int(insert_before)
        if not any(item.pk == anchor_id for item in items):
            raise ValueError('Block not found on this page')
        insert_index = next(
            index for index, item in enumerate(items) if item.pk == anchor_id
        )

    if insert_index >= len(items):
        return get_next_block_sort_order(page)

    for index, item in enumerate(items):
        if index < insert_index:
            new_order = index + 1
        else:
            new_order = index + 2
        if item.sort_order != new_order:
            ContentBlock.objects.filter(pk=item.pk).update(sort_order=new_order)

    return insert_index + 1


def create_content_block(
    page,
    resource_type,
    validated_data,
    write_serializer_class,
    insert_after=None,
    insert_before=None,
):
    block_type = BLOCK_RESOURCE_TYPES[resource_type]
    sort_order = resolve_insert_sort_order(
        page,
        insert_after=insert_after,
        insert_before=insert_before,
    )
    defaults = BLOCK_CREATE_DEFAULTS.get(block_type, {})

    instance = ContentBlock.objects.create(
        page=page,
        block_type=block_type,
        sort_order=sort_order,
        **defaults
    )

    write_serializer = write_serializer_class()
    write_serializer.update(instance, validated_data)
    return instance
