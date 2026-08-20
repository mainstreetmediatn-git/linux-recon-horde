# Database

Apply the migrations in order to the dedicated HORDE project. The foundation migration is idempotent for tables, indexes, functions, and the schema version row. The follow-up access migration grants the server-side service role access while revoking it from public and authenticated roles.

Add `horde` to the project's exposed Data API schemas before using the REST client. Keep the schema restricted to the service role; RLS remains enabled on every application table and no public policies are created.

After applying migrations, run Supabase security and performance advisors. Review any warning before enabling production execution. The worker should compare its expected schema version with `horde.schema_version` during startup. `SupabaseJobQueue` uses the database RPCs for atomic claim and lease recovery, so do not replace them with client-side select-then-update logic.
