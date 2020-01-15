from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline
from django import forms
from django.contrib import admin
from django.contrib.admin.options import TabularInline
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.initiatives.models import Initiative
from bluebottle.utils.widgets import SecureAdminURLFieldWidget
from .models import Category, CategoryContent


class CategoryContentInline(SortableStackedInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 'cols': 80})},
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    model = CategoryContent
    extra = 0
    max_num = 3


class CategoryInitiativesInline(TabularInline):
    model = Initiative.categories.through
    raw_id_fields = ('initiative', )
    extra = 0


class CategoryAdmin(AdminImageMixin, NonSortableParentAdmin):
    model = Category
    list_display = ('title', 'slug', 'initiatives')
    inlines = (CategoryContentInline, CategoryInitiativesInline)
    ordering = ['title']

    def initiatives(self, obj):
        url = reverse('admin:initiatives_initiative_changelist')
        count = Initiative.objects.filter(categories__id=obj.id).count()
        return format_html(
            '<a href="{}?categories__id={}">{} {}</a>',
            url, obj.id, count, _('initiatives'))


admin.site.register(Category, CategoryAdmin)
