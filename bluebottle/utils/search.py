from django.db.models import Case, When, IntegerField

from django_elasticsearch_dsl.search import Search as BaseSearch


class Search(BaseSearch):
    def to_queryset(self, keep_order=True):
        """
        This method return a django queryset from the an elasticsearch result.
        It cost a query to the sql db.

        Overriden to make it work with polymorphic models
        """
        s = self

        # Do not query again if the es result is already cached
        if not hasattr(self, '_response'):
            # We only need the meta fields with the models ids
            s = self.source(excludes=['*'])

        pks = [result._id for result in s]

        qs = self._model.objects.filter(pk__in=pks)

        if keep_order:

            # Annotate the queryset in order for ordering to work
            # with polymorphic models
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(pks)],
                output_field=IntegerField()
            )
            qs = qs.annotate(search_order=preserved_order).order_by('search_order')

        return qs
