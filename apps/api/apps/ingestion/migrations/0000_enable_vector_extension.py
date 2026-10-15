# Enable pgvector extension before any VectorField tables are created.
# PostgreSQL-only: skipped silently on SQLite test runs.

from django.db import migrations


def create_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def drop_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP EXTENSION IF EXISTS vector;")


class Migration(migrations.Migration):

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.RunPython(create_vector_extension, drop_vector_extension),
    ]
