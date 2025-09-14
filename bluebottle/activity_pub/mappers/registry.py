from typing import Dict, Type

from bluebottle.activity_pub.mappers.collect_activity import CollectActivityMapper
from bluebottle.activity_pub.mappers.date_activity import DateActivityMapper
from bluebottle.activity_pub.mappers.deadline_activity import DeadlineActivityMapper

from ..models import Event
from .base import ActivityMapper
from .deed import DeedMapper


class MapperRegistry:
    def __init__(self):
        self._mappers: Dict[Type, ActivityMapper] = {}

    def register(self, activity_type: Type, mapper: ActivityMapper):
        self._mappers[activity_type] = mapper

    def get_mapper(self, activity_type: Type) -> ActivityMapper:
        return self._mappers.get(activity_type)

    def to_event(self, activity) -> Event:
        mapper = self.get_mapper(type(activity))
        if not mapper:
            raise ValueError(f"No mapper found for {type(activity)}")
        return mapper.to_event(activity)


# Global registry
mapper_registry = MapperRegistry()

# Register mappers
from bluebottle.deeds.models import Deed
from bluebottle.time_based.models import DateActivity, DeadlineActivity

mapper_registry.register(Deed, DeedMapper())
mapper_registry.register(CollectActivityMapper, CollectActivityMapper())
mapper_registry.register(DateActivity, DateActivityMapper())
mapper_registry.register(DeadlineActivity, DeadlineActivityMapper())
