from bluebottle.activities.serializers import ActivityImageSerializer
from bluebottle.activity_links.models import LinkedActivity
from bluebottle.files.views import ImageContentView


class LinkedActivityImage(ImageContentView):
    queryset = LinkedActivity.objects
    field = 'image'
    allowed_sizes = ActivityImageSerializer.sizes
