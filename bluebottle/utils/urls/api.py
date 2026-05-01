from django.urls import path
from ..views import LanguageList

urlpatterns = [
    path('languages/', LanguageList.as_view(), name='utils_language_list'),
]
