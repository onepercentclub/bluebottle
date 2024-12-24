import json

import pika
from django.db import connection as db_connection

from bluebottle.deeds.models import Deed
from bluebottle.deeds.serializers import DeedPubSerializer, DeedParticipantPubSerializer

# RabbitMQ Configuration
RABBITMQ_HOST = 'localhost'
ACTIVITY_EXCHANGE = 'activities'
PARTICIPANT_EXCHANGE = 'participants'


def publish_activity(activity):
    """Publish an activity (create or update) to the RabbitMQ exchange."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Define tenant-specific exchange
    tenant_exchange = f"{ACTIVITY_EXCHANGE}.{db_connection.tenant.schema_name}"

    # Declare exchange as fanout
    channel.exchange_declare(exchange=tenant_exchange, exchange_type='fanout', durable=False)

    # Serialize activity data
    serializer_data = DeedPubSerializer(activity).to_representation(activity)
    message = json.dumps(serializer_data)

    # Publish message (routing_key is ignored in fanout exchanges)
    channel.basic_publish(exchange=tenant_exchange, routing_key="", body=message)
    print(f"[x] Published Activity: {message} to tenant exchange {tenant_exchange}")

    connection.close()


def publish_participant(participant):
    """Publish a participant signup to a tenant-specific queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    activity_platform = participant.activity.source_platform

    # Declare tenant-specific queue
    exchange = f"{PARTICIPANT_EXCHANGE}.{activity_platform}"
    data = DeedParticipantPubSerializer(participant).to_representation(participant)
    print(data)
    message = json.dumps(data)

    channel.basic_publish(exchange=exchange, routing_key='', body=message)
    print(f"[x] Published Signup: {message} to exchange {exchange}")

    connection.close()


def pub_deed():
    deed = Deed.objects.filter(status='open').first()
    print("Publishing deed")
    publish_activity(deed)
