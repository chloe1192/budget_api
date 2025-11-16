from django.db import migrations


def add_initial_balance_column(apps, schema_editor):
    # Only relevant for MySQL; for other DBs, Django's initial migration should have created the column
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        # Check if column exists in MySQL's information_schema
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
            """,
            ["api_service_user", "initial_balance"],
        )
        exists = cursor.fetchone()[0] > 0
        if not exists:
            cursor.execute(
                "ALTER TABLE api_service_user ADD COLUMN initial_balance DECIMAL(12,2) NOT NULL DEFAULT 0"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("api_service", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_initial_balance_column, migrations.RunPython.noop),
    ]
