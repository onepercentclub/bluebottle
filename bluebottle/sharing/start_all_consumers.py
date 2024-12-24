import os

import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bluebottle.settings.local')
django.setup()

import threading
from django.db import connection


def run_consumer_for_tenant(schema_name, consumer_function):
    """Run a specific consumer function for a tenant."""
    connection.set_schema(schema_name)
    try:
        consumer_function()
    except Exception as e:
        print(f"Error running consumer for tenant {schema_name}: {e}")
    finally:
        connection.set_schema_to_public()


def main():
    schemas = ['nlcares', 'onepercent', 'mars', 'dll', 'voor_je_buurt']
    from bluebottle.sharing.consumers import consume_activities, consume_participants

    for schema_name in schemas:
        # Start threads for each consumer for this tenant
        threading.Thread(target=run_consumer_for_tenant, args=(schema_name, consume_activities),
                         daemon=True).start()
        threading.Thread(target=run_consumer_for_tenant, args=(schema_name, consume_participants),
                         daemon=True).start()

    # Keep the main thread alive
    while True:
        pass


if __name__ == "__main__":
    main()
