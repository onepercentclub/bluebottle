import threading
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from tenant_schemas.utils import tenant_context, get_tenant_model
from bluebottle.sharing.models import PlatformConnection, SharedActivity
import pika
import json

ACTIVITY_EXCHANGE = "activities"
RABBITMQ_HOST = "localhost"


class Command(BaseCommand):
    help = "Start RabbitMQ consumers for all tenants"

    consumer_threads = {}
    thread_lock = threading.Lock()

    def handle(self, *args, **options):
        tenants = get_tenant_model().objects.filter(schema_name__in=['nlcares', 'dll', 'mars', 'onepercent']).all()

        for tenant in tenants:
            self.start_consumers_for_tenant(tenant)

        # Listen for model changes to restart consumers
        self.setup_signals()

        # Keep the main thread alive
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Stopping consumers...")

    def start_consumers_for_tenant(self, tenant):
        with tenant_context(tenant):
            consumer_name = connection.tenant.schema_name
            platforms = PlatformConnection.objects.all()

            if not platforms.exists():
                print(f"Tenant {consumer_name} has no platforms. Skipping.")
                return

            print(f"Starting consumers for Tenant {consumer_name}...")

            def start_consumer(platform):
                publisher_name = platform.platform
                tenant_exchange = f"{ACTIVITY_EXCHANGE}.{publisher_name}"
                queue_name = f"{consumer_name}_queue"

                connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST)
                connection = pika.BlockingConnection(connection_params)
                channel = connection.channel()
                channel.exchange_declare(exchange=tenant_exchange, exchange_type="fanout")
                channel.queue_declare(queue=queue_name)
                channel.queue_bind(exchange=tenant_exchange, queue=queue_name, routing_key="")

                def callback(ch, method, properties, body):
                    activity = json.loads(body)
                    print(f"[x] Received Activity: {activity} for {publisher_name}")
                    with tenant_context(tenant):
                        SharedActivity.objects.update_or_create(
                            platform=publisher_name,
                            remote_id=activity["id"],
                            defaults={
                                "title": activity["title"],
                                "data": activity,
                            },
                        )

                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                print(f"[*] Listening on queue {queue_name} for {tenant_exchange} from {publisher_name}")
                channel.start_consuming()

            with self.thread_lock:
                threads = []
                for platform in platforms:
                    thread = threading.Thread(target=start_consumer, args=(platform,), daemon=True)
                    threads.append(thread)
                    thread.start()

                self.consumer_threads[consumer_name] = threads

    def stop_consumers_for_tenant(self, tenant):
        consumer_name = tenant.schema_name
        with self.thread_lock:
            if consumer_name in self.consumer_threads:
                threads = self.consumer_threads.pop(consumer_name)
                for thread in threads:
                    if thread.is_alive():
                        print(f"Stopping thread for Tenant {consumer_name}...")
                        thread.join(timeout=1)

    def setup_signals(self):
        @receiver([post_save, post_delete], sender=PlatformConnection)
        def platform_connection_changed(sender, instance, **kwargs):
            tenant = instance.tenant  # Ensure `tenant` field exists on PlatformConnection
            print(f"PlatformConnection changed for Tenant {tenant.schema_name}. Restarting consumers...")
            self.stop_consumers_for_tenant(tenant)
            self.start_consumers_for_tenant(tenant)
