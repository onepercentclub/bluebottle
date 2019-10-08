from elasticsearch_dsl.query import MatchPhrasePrefix, Term, Nested, Bool
from rest_framework import filters


class TrigramFilter(filters.SearchFilter):

    def construct_search(self, field_name):
        return "%s__unaccent__trigram_similar" % field_name

    def get_search_terms(self, request):
        """
        Don't split into separate search terms
        """
        search = request.query_params.get(self.search_param, None)
        if search:
            return [search]
        return None


class ElasticSearchFilter(filters.SearchFilter):
    search_field = 'filter[search]'

    def filter_queryset(self, request, queryset, view):
        search = self.document.search()

        filter_fields = self.get_filter_fields(request)
        filters = [self.get_filter(request, field) for field in filter_fields] + self.get_default_filters(request)

        if filters:
            search = search.filter(Bool(must=filters))

        search_query = self.get_search_query(request)
        if search_query:
            search = search.query(search_query)

        sort = self.get_sort(request)
        if sort:
            try:
                scoring = getattr(self, 'get_sort_{}'.format(sort))(request)
                search = search.query(scoring)
            except AttributeError:
                search = search.sort(*sort)

        return (queryset, search)

    def get_filter_fields(self, request):
        return [
            field for field in self.filters if request.GET.get('filter[{}]'.format(field))
        ]

    def get_search_query(self, request):
        terms = request.GET.get(self.search_field)

        if terms:
            queries = []
            for field in self.search_fields:
                boost = self.boost.get(field, 1)
                if '.' in field:
                    path = field.split('.')[0]
                    query = Nested(
                        path=path,
                        query=MatchPhrasePrefix(
                            **{field: {'query': terms, 'boost': boost}}
                        )
                    )
                else:
                    query = MatchPhrasePrefix(**{field: {'query': terms, 'boost': boost}})

                queries.append(query)

            return Bool(should=queries)

    def get_filter(self, request, field):
        value = request.GET['filter[{}]'.format(field)]

        if '.' in field:
            path = field.split('.')[0]
            return Nested(path=path, query=Term(**{field: value}))

        else:
            try:
                return getattr(self, 'get_{}_filter'.format(field))(value, request)
            except AttributeError:
                return Term(**{field: value})

    def get_sort(self, request):
        sort = request.GET.get('sort')
        return self.sort_fields.get(sort)

    def get_default_filters(self, request):
        return []
