from django.forms import Select


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
