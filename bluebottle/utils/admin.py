from django.contrib import admin
from .models import Language

class LanguageAdmin(admin.ModelAdmin):
    model = Language
    list_display = ('code', 'language_name', 'native_name')

admin.site.register(Language, LanguageAdmin)
