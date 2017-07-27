from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin
from .models import Category, CategoryContent


class CategoryContentInline(admin.StackedInline):
    model = CategoryContent
    extra = 0
    max_num = 3


class CategoryAdmin(AdminImageMixin, admin.ModelAdmin):
    model = Category
    list_display = ('title', 'slug')
    inlines = (CategoryContentInline,)


admin.site.register(Category, CategoryAdmin)
