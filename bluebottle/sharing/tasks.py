from subprocess import run

from celery import shared_task


@shared_task
def start_consumer(schema_name):
    """
    Start consumers for a specific tenant schema.
    """
    result = run(
        ['./manage.py', 'start_consumers', '-s', schema_name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Failed to start consumers for {schema_name}: {result.stderr}")
    return f"Successfully started consumers for {schema_name}"
