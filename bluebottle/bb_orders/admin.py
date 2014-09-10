from django.contrib import admin
from bluebottle.utils.model_dispatcher import get_order_model

ORDER_MODEL = get_order_model()


class BaseOrderAdmin(admin.ModelAdmin):
    model = get_order_model()

# if you want to display more fields, unregister the model first, define a new admin class
# (possibly inheriting from BaseProjectAdmin), and then re-register it
admin.site.register(ORDER_MODEL, BaseOrderAdmin)

