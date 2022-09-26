from django.forms import Select
from bluebottle.utils.utils import reverse_signed


class ImageWidget(Select):
    template_name = 'widgets/image.html'

    def get_context(self, name, value, attrs):
        context = super(ImageWidget, self).get_context(name, value, attrs)
        if value:
            from bluebottle.files.models import Image
            context['file'] = Image.objects.get(pk=value).file
        else:
            context['file'] = None
        return context


class DocumentWidget(Select):
    template_name = 'widgets/document.html'

    def get_context(self, name, value, attrs):
        context = super(DocumentWidget, self).get_context(name, value, attrs)
        if value:
            from bluebottle.files.models import Document
            context['file'] = Document.objects.get(pk=value).file
        else:
            context['file'] = None
        return context


class PrivateDocumentWidget(Select):
    template_name = 'widgets/document.html'

    def get_context(self, name, value, attrs):
        context = super(PrivateDocumentWidget, self).get_context(name, value, attrs)

        if value:
            from bluebottle.files.models import PrivateDocument
            document = PrivateDocument.objects.get(pk=value)
            context['download_link'] = reverse_signed(
                self.attrs['view_name'],
                args=(getattr(document, f"{self.attrs['related_field']}_set").first().pk, )
            )
        else:
            context['download_link'] = None
        return context
