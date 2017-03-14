from rest_framework import filters


class TrigramFilter(filters.SearchFilter):

    def construct_search(self, field_name):
        return "%s__trigram_similar" % field_name
