from django.forms import Select

from bluebottle.files.models import Image


class ImageWidget(Select):
    template_name = 'widgets/image.html'

    def get_context(self, name, value, attrs):
        context = super(ImageWidget, self).get_context(name, value, attrs)
        if value:
            context['file'] = Image.objects.get(pk=value).file
        else:
            context['file'] = None
        return context
