from django import forms
from django.contrib.admin.options import TabularInline
from django.db import models
from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.projects.models import Project
from .models import Category, CategoryContent
from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline


class CategoryContentInline(SortableStackedInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 'cols': 80})},
    }
    model = CategoryContent
    extra = 0
    max_num = 3


class CategoryProjectsInline(TabularInline):
    model = Project.categories.through
    raw_id_fields = ('project', )
    extra = 0


class CategoryAdmin(AdminImageMixin, NonSortableParentAdmin):
    model = Category
    list_display = ('title', 'slug')
    inlines = (CategoryContentInline, CategoryProjectsInline)


admin.site.register(Category, CategoryAdmin)
