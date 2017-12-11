from django.dispatch import Signal

platform_event = Signal(providing_args=["obj", "name"])
