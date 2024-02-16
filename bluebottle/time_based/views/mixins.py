from django.db.models import Q

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.activities.models import Activity


class AnonimizeMembersMixin:
    @property
    def owners(self):
        return []

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        if self.request.user and self.request.user.is_authenticated and (
                self.request.user in self.owners or
                self.request.user.is_staff or
                self.request.user.is_superuser
        ):
            context['display_member_names'] = 'full_name'

        return context


class CreatePermissionMixin:
    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(user=self.request.user)


class FilterRelatedUserMixin:
    @property
    def owners(self):
        if 'activity_id' in self.kwargs:
            activity = Activity.objects.get(pk=self.kwargs['activity_id'])
            return [activity.owner] + list(activity.initiative.activity_managers.all())

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user) |
                    Q(activity__owner=self.request.user) |
                    Q(activity__initiative__activity_manager=self.request.user) |
                    Q(status__in=('accepted', 'succeeded',))
                ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
            ).order_by('-id')

        return queryset
