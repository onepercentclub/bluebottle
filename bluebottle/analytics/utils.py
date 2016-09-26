from importlib import import_module

from django.conf import settings

from celery import shared_task


@shared_task
def queue_analytics_record(timestamp, tags={}, fields={}):
    # Get the default backend for analytics
    def get_handler_class(handler): 
        try:
            # try to call handler
            parts = handler.split('.')
            module_path, class_name = '.'.join(parts[:-1]), parts[-1]
            module = import_module(module_path)
            cls = getattr(module, class_name)

            return cls

        except (ImportError, AttributeError) as e:
            error_message = "Could not import '%s'. %s: %s." % (handler, e.__class__.__name__, e)
            raise Exception(error_message)

    try:
        # TODO: logging to multiple backends could happen here, eg
        #       to influxdb and to log file.
        backend = settings.ANALYTICS_BACKENDS['default']
        handler_class = backend['handler_class']
    except AttributeError:
        return # TODO: add some logging

    handler = get_handler_class(handler_class)(conf=backend)
    handler.process(timestamp, tags, fields)
