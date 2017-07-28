from django import forms
from django.db import models
from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin
from .models import Category, CategoryContent


class CategoryContentInline(admin.StackedInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 'cols': 80})},
    }
    model = CategoryContent
    extra = 0
    max_num = 3
    exclude = ('created', 'updated')


class CategoryAdmin(AdminImageMixin, admin.ModelAdmin):
    model = Category
    list_display = ('title', 'slug')
    inlines = (CategoryContentInline,)


admin.site.register(Category, CategoryAdmin)
