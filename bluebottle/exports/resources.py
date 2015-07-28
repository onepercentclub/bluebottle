from exportdb.exporter import ExportModelResource


class DateRangeResource(ExportModelResource):
    range_field = 'created'
    select_related = None

    def get_queryset(self):
        qs = super(DateRangeResource, self).get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        frm, to = self.kwargs.get('from_date'), self.kwargs.get('to_date')
        return qs.filter(**{'%s__range' % self.range_field: (frm, to)})


class UserResource(DateRangeResource):
    range_field = 'date_joined'
    select_related = ('location',)


class ProjectResource(DateRangeResource):
    select_related = ('status', 'owner', 'location',)


class TaskResource(DateRangeResource):
    select_related = ('project', 'author', 'location')


class TaskMemberResource(DateRangeResource):
    select_related = ('member', 'task', 'task__project', 'member__location')


class DonationResource(DateRangeResource):
    select_related = ('order', 'order__user', 'order__user__location', 'project', 'fundraiser')
