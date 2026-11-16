import uuid

from django.db import migrations, models


# (table, column) pairs that hold an AuthenticationMethod primary key, either
# directly or through one of the polymorphic child tables.
UUID_COLUMNS = [
    ('members_authenticationmethod', 'id'),
    ('members_passwordauthentication', 'authenticationmethod_ptr_id'),
    ('members_facebookauthentication', 'authenticationmethod_ptr_id'),
    ('members_googleauthentication', 'authenticationmethod_ptr_id'),
    ('members_samlauthentication', 'authenticationmethod_ptr_id'),
    ('members_samlsegmentmapping', 'authentication_method_id'),
    ('members_passwordauthentication_translation', 'master_id'),
]


def convert_to_uuid(apps, schema_editor):
    """
    Postgres can not cast integer to uuid, and Django's AlterField does not
    update foreign keys that point to the child tables. So: drop the foreign
    keys, convert every column with the same deterministic int -> uuid mapping
    (so the relations stay intact), and re-create the foreign keys.
    """
    connection = schema_editor.connection
    quote = schema_editor.quote_name
    columns = set(UUID_COLUMNS)

    with connection.cursor() as cursor:
        foreign_keys = []
        for table in {table for table, _ in UUID_COLUMNS}:
            constraints = connection.introspection.get_constraints(cursor, table)
            for name, constraint in constraints.items():
                if (
                    constraint['foreign_key'] and
                    len(constraint['columns']) == 1 and
                    (table, constraint['columns'][0]) in columns
                ):
                    foreign_keys.append(
                        (table, name, constraint['columns'][0], constraint['foreign_key'])
                    )

        for table, name, _, _ in foreign_keys:
            schema_editor.execute(
                f'ALTER TABLE {quote(table)} DROP CONSTRAINT {quote(name)}'
            )

        schema_editor.execute(
            'ALTER TABLE "members_authenticationmethod" '
            'ALTER COLUMN "id" DROP IDENTITY IF EXISTS, '
            'ALTER COLUMN "id" DROP DEFAULT'
        )

        for table, column in UUID_COLUMNS:
            schema_editor.execute(
                f'ALTER TABLE {quote(table)} ALTER COLUMN {quote(column)} '
                f'TYPE uuid USING lpad(to_hex({quote(column)}), 32, \'0\')::uuid'
            )

        for table, name, column, (target_table, target_column) in foreign_keys:
            schema_editor.execute(
                f'ALTER TABLE {quote(table)} ADD CONSTRAINT {quote(name)} '
                f'FOREIGN KEY ({quote(column)}) '
                f'REFERENCES {quote(target_table)} ({quote(target_column)}) '
                'DEFERRABLE INITIALLY DEFERRED'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0122_alter_member_primary_language_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='authenticationmethod',
                    name='id',
                    field=models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(convert_to_uuid),
            ],
        ),
    ]
