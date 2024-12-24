import json

import pika
from django.db import connection as db_connection

from bluebottle.clients.utils import LocalTenant
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.sharing.models import PlatformConnection, SharedActivity

# RabbitMQ Configuration
RABBITMQ_HOST = 'localhost'
ACTIVITY_EXCHANGE = 'activities'
PARTICIPANT_EXCHANGE = 'participants'

import threading


def consume_activities():
    platforms = PlatformConnection.objects.all()
    consumer_name = db_connection.tenant.schema_name
    tenant = db_connection.tenant
    if not platforms.count():
        print(f'Tenant {consumer_name} has no platforms specified.')
        return

    print(f'Tenant {consumer_name} listening to {platforms.count()} platforms.')

    def start_consumer_for_platform(platform):
        publisher_name = platform.platform
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        tenant_exchange = f"{ACTIVITY_EXCHANGE}.{publisher_name}"
        channel.exchange_declare(exchange=tenant_exchange, exchange_type='fanout')

        queue_name = f"{consumer_name}_queue"
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=tenant_exchange, queue=queue_name, routing_key='')

        def callback(ch, method, properties, body):
            activity = json.loads(body)
            print(f"[x] Received Activity: {activity} for {publisher_name}")
            with LocalTenant(tenant):
                SharedActivity.objects.update_or_create(
                    platform=publisher_name,
                    remote_id=activity['id'],
                    defaults={
                        'title': activity['title'],
                        'data': activity
                    }
                )

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"[*] {consumer_name} listening on queue {queue_name} for "
              f"activities on {tenant_exchange} from {publisher_name}."
              )
        channel.start_consuming()

    # Start a thread for each platform
    threads = []
    for platform in platforms:
        thread = threading.Thread(target=start_consumer_for_platform, args=(platform,), daemon=True)
        threads.append(thread)
        thread.start()

    # Keep the main thread alive to allow the consumer threads to run
    for thread in threads:
        thread.join()


def consume_participants():
    """Consume participant signup messages for the current tenant using a fanout exchange."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    tenant_name = db_connection.tenant.schema_name
    tenant = db_connection.tenant

    # Tenant-specific exchange
    tenant_exchange = f"{PARTICIPANT_EXCHANGE}.{tenant_name}"

    # Declare the tenant-specific exchange
    channel.exchange_declare(exchange=tenant_exchange, exchange_type='fanout')

    # Declare a non-durable, exclusive, auto-delete queue for this consumer
    result = channel.queue_declare(queue='', exclusive=True)
    temp_queue_name = result.method.queue

    # Bind the temporary queue to the tenant-specific exchange
    channel.queue_bind(exchange=tenant_exchange, queue=temp_queue_name)

    def callback(ch, method, properties, body):
        try:
            with LocalTenant(tenant):
                data = json.loads(body)
                print(f"[x] Received Signup for {tenant_name}: {data}")
                deed = Deed.objects.get(id=data['activity_id'])
                participant, _ = DeedParticipant.objects.update_or_create(
                    source_platform=data['platform'],
                    remote_id=data['remote_id'],
                    activity=deed,
                    defaults={
                        'remote_name': data['name']
                    }
                )
        except Exception as e:
            print(f"Error processing signup for {tenant_name}: {e}")

    # Consume messages from the temporary queue
    channel.basic_consume(queue=temp_queue_name, on_message_callback=callback, auto_ack=True)
    print(f'[*] {tenant_name} listening for signups on exchange {tenant_exchange}.')
    channel.start_consuming()
