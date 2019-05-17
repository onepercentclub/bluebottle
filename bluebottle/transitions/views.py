from rest_framework_json_api.parsers import JSONParser

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.utils.permissions import (
    ResourceOwnerPermission, OneOf, ResourcePermission
)
from bluebottle.utils.views import CreateAPIView


class TransitionList(CreateAPIView):
    parser_classes = (JSONParser, )
    renderer_classes = (BluebottleJSONAPIRenderer, )

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
