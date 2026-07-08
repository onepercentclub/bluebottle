import os

from django.conf import settings
from django.http import Http404
from django.views.static import serve

from bluebottle.utils.storage import TenantFileSystemStorage


def serve_tenant_media(request, path):
    storage = TenantFileSystemStorage()
    document_root = storage.location

    if not os.path.exists(os.path.join(document_root, path)):
        fallback_root = settings.MEDIA_ROOT
        if fallback_root != document_root and os.path.exists(os.path.join(fallback_root, path)):
            document_root = fallback_root
        else:
            raise Http404()

    return serve(request, path, document_root=document_root)
