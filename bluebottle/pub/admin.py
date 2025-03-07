from django.contrib import admin

from bluebottle.pub.models import Actor, Platform, RemoteActor


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('domain', 'created', 'updated')
    search_fields = ('domain',)
    raw_id_fields = ('owner',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('username', 'platform', 'user', 'created', 'updated')
    search_fields = ('username', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    list_filter = ('platform',)
    readonly_fields = ('actor_uri',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'username', 'platform')
        return self.readonly_fields


@admin.register(RemoteActor)
class RemoteActorAdmin(admin.ModelAdmin):
    list_display = ('username', 'domain', 'actor_uri', 'created', 'updated')
    search_fields = ('username', 'domain', 'actor_uri')
    readonly_fields = ('created', 'updated')
