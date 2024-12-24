from .tasks import start_consumer


def start_all_consumers():
    """
    Start consumers for all tenant schemas asynchronously using Celery tasks.
    """
    schemas = ['nlcares', 'dll', 'mars', 'onepercent',
               'voor_je_buurt']  # Replace with dynamic tenant retrieval if needed
    for schema in schemas:
        start_consumer.delay(schema)  # Trigger the Celery task
