from rest_framework import serializers

from bluebottle.activity_pub.models import DoGoodEvent, GoodDeed


class BaseUpdateSyncSerializer(serializers.Serializer):
    def sync(self):
        raise NotImplementedError


class GoodDeedUpdateSyncSerializer(BaseUpdateSyncSerializer):
    def sync(self):
        from bluebottle.deeds.models import Deed
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer

        event_good_deed = self.context['object']
        adapter = self.context['adapter']

        for activity in event_good_deed.adopted_activities.all():
            activity = activity.get_real_instance()
            if not isinstance(activity, Deed):
                continue
            payload = {
                'type': 'GoodDeed',
                'name': event_good_deed.name,
                'summary': event_good_deed.summary,
                'start_time': getattr(event_good_deed, 'start_time', None),
                'end_time': getattr(event_good_deed, 'end_time', None),
            }
            serializer = FederatedActivitySerializer(
                instance=activity,
                data=payload,
                partial=True,
                context=self.context,
            )
            serializer.is_valid(raise_exception=True)
            deed = serializer.save(owner=activity.owner)
            adapter.create_or_update_event(deed)

        return True


class DoGoodEventUpdateSyncSerializer(BaseUpdateSyncSerializer):
    def sync(self):
        from bluebottle.activity_pub.adapters import _sync_adopted_date_slots_from_source
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
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
            payload = {
                'type': 'DoGoodEvent',
                'name': event_do_good.name,
                'summary': event_do_good.summary,
                'capacity': event_do_good.capacity,
            }
            serializer = FederatedActivitySerializer(
                instance=activity,
                data=payload,
                partial=True,
                context=self.context,
            )
            serializer.is_valid(raise_exception=True)
            updated_activity = serializer.save(owner=activity.owner)
            if isinstance(updated_activity, DateActivity):
                _sync_adopted_date_slots_from_source(event_do_good, source_date, updated_activity)
            adapter.create_or_update_event(updated_activity)

        return True


class PolymorphicUpdateSyncSerializer(BaseUpdateSyncSerializer):
    serializer_map = {
        GoodDeed: GoodDeedUpdateSyncSerializer,
        DoGoodEvent: DoGoodEventUpdateSyncSerializer,
    }

    def sync(self):
        obj = self.context['object']
        for model_class, serializer_class in self.serializer_map.items():
            if isinstance(obj, model_class):
                serializer = serializer_class(context=self.context)
                return serializer.sync()
        return False
