import factory
from django.contrib.contenttypes.models import ContentType
from fluent_contents.models import Placeholder
from fluent_contents.plugins.text.models import TextItem

from bluebottle.test.factory_models.pages import PageFactory


class ContentItemMixin(object):

    def _create(cls, model_class, *args, **kwargs):
        page = kwargs.pop('page')
        page_ctype = ContentType.objects.get_for_model(page)
        slot = 'blog_contents'
        placeholder, _created = Placeholder.objects.get_or_create(
            parent_id=page.pk,
            parent_type_id=page_ctype.pk,
            slot=slot,
            role='m'
        )
        block_ctype = ContentType.objects.get_for_model(model_class)
        block, _created = model_class.objects.create_for_placeholder(
            placeholder,
            polymorphic_ctype=block_ctype,
            **kwargs
        )
        return block


class TextItemFactory(ContentItemMixin, factory.DjangoModelFactory):
    class Meta(object):
        model = TextItem

    language = 'en'
    text = factory.Faker('text')
    page = factory.SubFactory(PageFactory)
