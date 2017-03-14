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
