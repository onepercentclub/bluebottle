from bluebottle.terms.models import Terms
from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE


class TermsForm(forms.ModelForm):
    contents = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 40}))

    class Meta:
        model = Terms


class TermsAdmin(admin.ModelAdmin):
    model = Terms
    form = TermsForm
    raw_id_fields = ('author', )

admin.site.register(Terms, TermsAdmin)
