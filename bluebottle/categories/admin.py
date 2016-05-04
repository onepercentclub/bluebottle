from django.contrib import admin

from sorl.thumbnail.admin import AdminImageMixin

from .models import Category


class CategoryAdmin(AdminImageMixin, admin.ModelAdmin):
    model = Category

admin.site.register(Category, CategoryAdmin)
