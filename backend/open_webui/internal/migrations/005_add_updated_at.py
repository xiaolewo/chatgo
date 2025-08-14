"""Peewee migrations -- 002_add_local_sharing.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    if isinstance(database, pw.SqliteDatabase):
        migrate_sqlite(migrator, database, fake=fake)
    else:
        migrate_external(migrator, database, fake=fake)


def migrate_sqlite(migrator: Migrator, database: pw.Database, *, fake=False):
    # Adding fields created_at and updated_at to the 'chat' table
    try:
        migrator.add_fields(
            "chat",
            created_at=pw.DateTimeField(null=True),  # Allow null for transition
            updated_at=pw.DateTimeField(null=True),  # Allow null for transition
        )
        print("✅ SQLite: 成功添加 created_at, updated_at 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  SQLite: created_at/updated_at 字段已存在，跳过添加")
        else:
            raise e

    # Populate the new fields from an existing 'timestamp' field
    migrator.sql(
        "UPDATE chat SET created_at = timestamp, updated_at = timestamp WHERE timestamp IS NOT NULL"
    )

    # Now that the data has been copied, remove the original 'timestamp' field
    migrator.remove_fields("chat", "timestamp")

    # Update the fields to be not null now that they are populated
    migrator.change_fields(
        "chat",
        created_at=pw.DateTimeField(null=False),
        updated_at=pw.DateTimeField(null=False),
    )


def migrate_external(migrator: Migrator, database: pw.Database, *, fake=False):
    # Adding fields created_at and updated_at to the 'chat' table
    try:
        migrator.add_fields(
            "chat",
            created_at=pw.BigIntegerField(null=True),  # Allow null for transition
            updated_at=pw.BigIntegerField(null=True),  # Allow null for transition
        )
        print("✅ External DB: 成功添加 created_at, updated_at 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  External DB: created_at/updated_at 字段已存在，跳过添加")
        else:
            raise e

    # Populate the new fields from an existing 'timestamp' field
    migrator.sql(
        "UPDATE chat SET created_at = timestamp, updated_at = timestamp WHERE timestamp IS NOT NULL"
    )

    # Now that the data has been copied, remove the original 'timestamp' field
    migrator.remove_fields("chat", "timestamp")

    # Update the fields to be not null now that they are populated
    migrator.change_fields(
        "chat",
        created_at=pw.BigIntegerField(null=False),
        updated_at=pw.BigIntegerField(null=False),
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    if isinstance(database, pw.SqliteDatabase):
        rollback_sqlite(migrator, database, fake=fake)
    else:
        rollback_external(migrator, database, fake=fake)


def rollback_sqlite(migrator: Migrator, database: pw.Database, *, fake=False):
    # Recreate the timestamp field initially allowing null values for safe transition
    try:
        migrator.add_fields("chat", timestamp=pw.DateTimeField(null=True))
        print("✅ SQLite Rollback: 成功添加 timestamp 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  SQLite Rollback: timestamp 字段已存在，跳过添加")
        else:
            raise e

    # Copy the earliest created_at date back into the new timestamp field
    # This assumes created_at was originally a copy of timestamp
    migrator.sql("UPDATE chat SET timestamp = created_at")

    # Remove the created_at and updated_at fields
    migrator.remove_fields("chat", "created_at", "updated_at")

    # Finally, alter the timestamp field to not allow nulls if that was the original setting
    migrator.change_fields("chat", timestamp=pw.DateTimeField(null=False))


def rollback_external(migrator: Migrator, database: pw.Database, *, fake=False):
    # Recreate the timestamp field initially allowing null values for safe transition
    try:
        migrator.add_fields("chat", timestamp=pw.BigIntegerField(null=True))
        print("✅ External Rollback: 成功添加 timestamp 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  External Rollback: timestamp 字段已存在，跳过添加")
        else:
            raise e

    # Copy the earliest created_at date back into the new timestamp field
    # This assumes created_at was originally a copy of timestamp
    migrator.sql("UPDATE chat SET timestamp = created_at")

    # Remove the created_at and updated_at fields
    migrator.remove_fields("chat", "created_at", "updated_at")

    # Finally, alter the timestamp field to not allow nulls if that was the original setting
    migrator.change_fields("chat", timestamp=pw.BigIntegerField(null=False))
