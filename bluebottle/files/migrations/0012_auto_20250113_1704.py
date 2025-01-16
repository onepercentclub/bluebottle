from django.db import migrations
from django.core.files.images import ImageFile

from bluebottle.files.utils import get_default_cropbox


def set_cropbox(apps, schema_editor):
    Image = apps.get_model('files', 'Image')
    for image in Image.objects.all():
        if image.file.storage.exists(image.file.name):
            with image.file.open():
                image.cropbox = get_default_cropbox(ImageFile(image.file))

                image.save()


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0011_image_cropbox'),
    ]

    operations = [
    ]
