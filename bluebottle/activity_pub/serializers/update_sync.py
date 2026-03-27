from rest_framework import serializers

from bluebottle.activity_pub.models import DoGoodEvent, GoodDeed, SubEvent


class BaseUpdateSyncSerializer(serializers.Serializer):
    def sync(self):
        raise NotImplementedError


class GoodDeedUpdateSyncSerializer(BaseUpdateSyncSerializer):
    def sync(self):
        from bluebottle.deeds.models import Deed

        event_good_deed = self.context['object']
        adapter = self.context['adapter']

        for activity in event_good_deed.adopted_activities.all():
            activity = activity.get_real_instance()
            if not isinstance(activity, Deed):
                continue
            deed = activity
            update_fields = []
            if event_good_deed.name != deed.title:
                deed.title = event_good_deed.name
                update_fields.append('title')
            if (
                getattr(event_good_deed, 'start_time', None) is not None and
                deed.start != event_good_deed.start_time.date()
            ):
                deed.start = event_good_deed.start_time.date()
                update_fields.append('start')
            if (
                getattr(event_good_deed, 'end_time', None) is not None and
                deed.end != event_good_deed.end_time.date()
            ):
                deed.end = event_good_deed.end_time.date()
                update_fields.append('end')
            if event_good_deed.summary is not None:
                try:
                    if getattr(deed.description, 'html', None) != event_good_deed.summary:
                        if hasattr(deed.description, 'html'):
                            deed.description.html = event_good_deed.summary
                            update_fields.append('description')
                except (AttributeError, TypeError):
                    pass
            if update_fields:
                deed.save(update_fields=update_fields)
            adapter.create_or_update_event(deed)

        return True


class DoGoodEventUpdateSyncSerializer(BaseUpdateSyncSerializer):
    def sync(self):
        from bluebottle.activity_pub.models import Event as ActivityPubEvent
        from bluebottle.activity_pub.adapters import _sync_adopted_date_slots_from_source
        from bluebottle.time_based.models import DateActivity, DeadlineActivity

        event_do_good = self.context['object']
        adapter = self.context['adapter']

        source_date = None
        source_bb_activity = event_do_good.activity
        if source_bb_activity is not None:
            real = source_bb_activity.get_real_instance()
            if isinstance(real, (DateActivity, DeadlineActivity)):
                source_date = real

        for activity in event_do_good.adopted_activities.all():
            activity = activity.get_real_instance()
            if not isinstance(activity, (DateActivity, DeadlineActivity)):
                continue

            try:
                adopted_ev = activity.event
            except ActivityPubEvent.DoesNotExist:
                adopted_ev = None
            if adopted_ev is not None and event_do_good.capacity != adopted_ev.capacity:
                adopted_ev.capacity = event_do_good.capacity
                adopted_ev.save(update_fields=['capacity'])
            cap = event_do_good.capacity
            if cap is not None and cap != activity.capacity:
                activity.capacity = cap
                activity.save(update_fields=['capacity'])
            elif source_date is not None and source_date.capacity != activity.capacity:
                activity.capacity = source_date.capacity
                activity.save(update_fields=['capacity'])
            remote_count = event_do_good.contributor_count or 0
            if activity.synced_contributor_count != remote_count:
                activity.synced_contributor_count = remote_count
                activity.save(update_fields=['synced_contributor_count'])
            if event_do_good.name != activity.title:
                activity.title = event_do_good.name
                activity.save(update_fields=['title'])
            if event_do_good.summary is not None:
                try:
                    if getattr(activity.description, 'html', None) != event_do_good.summary:
                        if hasattr(activity.description, 'html'):
                            activity.description.html = event_do_good.summary
                            activity.save(update_fields=['description'])
                except (AttributeError, TypeError):
                    pass
            if isinstance(activity, DateActivity):
                _sync_adopted_date_slots_from_source(event_do_good, source_date, activity)
            adapter.create_or_update_event(activity)

        return True


class SubEventUpdateSyncSerializer(BaseUpdateSyncSerializer):
    def sync(self):
        from bluebottle.activity_pub.adapters import _sync_slot_from_subevent

        sub_event = self.context['object']
        _sync_slot_from_subevent(sub_event)
        return True


class PolymorphicUpdateSyncSerializer(BaseUpdateSyncSerializer):
    serializer_map = {
        GoodDeed: GoodDeedUpdateSyncSerializer,
        DoGoodEvent: DoGoodEventUpdateSyncSerializer,
        SubEvent: SubEventUpdateSyncSerializer,
    }

    def sync(self):
        obj = self.context['object']
        for model_class, serializer_class in self.serializer_map.items():
            if isinstance(obj, model_class):
                serializer = serializer_class(context=self.context)
                return serializer.sync()
        return False
