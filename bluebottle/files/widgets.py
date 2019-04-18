from django.forms import Select

from bluebottle.files.models import Image


class ImageWidget(Select):
    template_name = 'widgets/image.html'

    def get_context(self, name, value, attrs):
        context = super(ImageWidget, self).get_context(name, value, attrs)
        context['file'] = Image.objects.get(pk=value).file
        return context
