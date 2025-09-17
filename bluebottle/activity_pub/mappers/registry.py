from typing import Dict, Type

from bluebottle.activity_pub.mappers.collect_activity import CollectActivityMapper
from bluebottle.activity_pub.mappers.date_activity import DateActivityMapper
from bluebottle.activity_pub.mappers.deadline_activity import DeadlineActivityMapper
from .base import ActivityMapper
from .deed import DeedMapper
from bluebottle.deeds.models import Deed
from bluebottle.time_based.models import DateActivity, DeadlineActivity, PeriodicActivity, ScheduleActivity


class MapperRegistry:
    _mappers = {}

    def __init__(self):
        self._mappers[Type, ActivityMapper] = {}

    def register(self, activity_type, mapper):
        self._mappers[activity_type] = mapper

    def get_mapper(self, activity_type):
        return self._mappers.get(activity_type)

    def to_event(self, activity):
        mapper = self.get_mapper(type(activity))
        if not mapper:
            raise ValueError(f"No mapper found for {type(activity)}")
        return mapper.to_event(activity)

    def to_activity(self, event, user):
        if hasattr(event, 'subEvent'):
            if getattr(event, 'repeatFrequency', None):
                mapper = self.get_mapper(PeriodicActivity)
            elif getattr(event, 'duration', None):
                mapper = self.get_mapper(ScheduleActivity)
            else:
                mapper = self.get_mapper(DateActivity)
        elif getattr(event, 'duration', None):
            mapper = self.get_mapper(DeadlineActivity)
        else:
            mapper = self.get_mapper(Deed)
        return mapper.to_activity(event, user)


mapper_registry = MapperRegistry()

mapper_registry.register(Deed, DeedMapper())
mapper_registry.register(CollectActivityMapper, CollectActivityMapper())
mapper_registry.register(DateActivity, DateActivityMapper())
mapper_registry.register(DeadlineActivity, DeadlineActivityMapper())
