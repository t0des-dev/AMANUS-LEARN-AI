# Add pg_trgm GIN index to accelerate ILIKE / icontains lexical search on chunk content.
# PostgreSQL-only: skipped silently on SQLite test runs.

from django.db import migrations


def create_trgm_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ingestion_documentchunk_content_trgm "
            "ON ingestion_documentchunk USING gin (content gin_trgm_ops);"
        )


def drop_trgm_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS ingestion_documentchunk_content_trgm;")


class Migration(migrations.Migration):

    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_trgm_index, drop_trgm_index),
    ]
