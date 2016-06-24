from rest_framework.pagination import PageNumberPagination


class BluebottlePagination(PageNumberPagination):
    page_size = 10
