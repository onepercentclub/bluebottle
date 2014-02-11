from django.contrib import admin
from .models import ContactMessage


class ContactMessageAdmin(admin.ModelAdmin):
    model = ContactMessage
    list_display = ('message', 'name', 'email', 'creation_date', 'status')
    list_filter = ('status', )
    search_fields = ('message', 'name', 'email')
    raw_id_fields = ('author', )

admin.site.register(ContactMessage, ContactMessageAdmin)