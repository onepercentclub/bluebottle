# Generated by Django 2.2.24 on 2022-09-22 07:14

from django.db import migrations, connection


def create_update_function(apps, schema_editor):
    function_sql = """
        CREATE OR REPLACE FUNCTION refresh_union_table(my_table text, my_view text) RETURNS void AS $$
        DECLARE
          schema TEXT;
          col TEXT;
          sql TEXT := '';
          column_names TEXT := '';
        BEGIN
          FOR col IN SELECT DISTINCT column_name FROM information_schema.columns
            WHERE table_name = my_table AND table_schema in (select schema_name from public.clients_client)
            AND column_name NOT IN ('column_name', 'password', 'tenant', 'place')
          LOOP
          column_names := column_names || format(', %I', col);
          END LOOP;
          FOR schema IN SELECT schema_name FROM clients_client
          LOOP
            sql := sql || format('SELECT ''%I'' AS tenant', schema) || column_names || format(' FROM %I.%I UNION ALL ', schema, my_table);
          END LOOP;
          EXECUTE
            format('CREATE OR REPLACE VIEW %I AS ', my_view) || left(sql, -11);
        END
        $$ LANGUAGE plpgsql;
    """

    if connection.tenant.schema_name == 'public':
        schema_editor.execute(function_sql, params=None)

class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_auto_20201118_1535'),
    ]

    operations = [
        migrations.RunPython(create_update_function, migrations.RunPython.noop),
    ]
