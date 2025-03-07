from django.urls import path

from . import views

app_name = "pub"

urlpatterns = [
    path("actor", views.ActivityPubViewSet.as_view({"get": "get_actor"}), name="actor"),
    path(
        "outbox", views.ActivityPubViewSet.as_view({"get": "get_outbox"}), name="outbox"
    ),
    path(
        "registration",
        views.ActivityPubViewSet.as_view(
            {"get": "get_registrations", "post": "add_registration"}
        ),
        name="registration",
    ),
    path("inbox", views.ActivityPubViewSet.as_view({"post": "inbox"}), name="inbox"),
]
