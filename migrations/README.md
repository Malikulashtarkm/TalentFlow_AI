# Migration Roadmap

The current project keeps schema DDL in `DDL.sql` and deployment logic in `deploy_schema.py`. For a production-style submission, the next step is to move database changes into versioned migrations.

Recommended path:

1. Introduce Alembic.
2. Generate an initial migration from `DDL.sql`.
3. Move future schema changes into ordered migration files.
4. Keep `deploy_schema.py` as a thin wrapper around migration execution.
5. Run migrations before seed scripts and ELT flows in the demo checklist.

This prevents duplicate schema definitions from drifting apart and gives reviewers a clear database change history.
