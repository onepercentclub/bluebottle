from django import forms
from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin
from tinymce.widgets import TinyMCE
from .models import Category, CategoryContent


class CatergoryContentForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=TinyMCE())

    class Meta:
        mode = CategoryContent
        exclude = ()


class CategoryContentInline(admin.StackedInline):
    model = CategoryContent
    form = CatergoryContentForm
    extra = 0
    max_num = 3


class CategoryAdmin(AdminImageMixin, admin.ModelAdmin):
    model = Category
    list_display = ('title', 'slug')
    inlines = (CategoryContentInline,)


admin.site.register(Category, CategoryAdmin)
