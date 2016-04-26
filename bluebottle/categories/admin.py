from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from sorl.thumbnail.admin import AdminImageMixin

from .models import Category


class CategoryAdmin(AdminImageMixin, TranslationAdmin):
    model = Category

admin.site.register(Category, CategoryAdmin)


