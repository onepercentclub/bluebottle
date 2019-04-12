from django.contrib import admin
from django.utils.html import format_html

from bluebottle.files.models import Image, Document


class FileAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', )

    def get_form(self, request, obj=None, **kwargs):
        form = super(FileAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['owner'].initial = request.user
        return form

    fields = ('file', 'owner')


class ImageAdmin(FileAdmin):
    model = Image
    readonly_fields = ('image', )
    fields = ('file', 'image', 'owner')

    def image(self, obj):
        return format_html('<img src="{url}" height=200 />', url=obj.file.url)


admin.site.register(Image, ImageAdmin)


class DocumentAdmin(FileAdmin):
    model = Document


admin.site.register(Document, DocumentAdmin)
