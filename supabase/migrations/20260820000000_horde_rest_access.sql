-- Expose the dedicated horde schema only to the server-side service role.
-- The schema must also be added to Supabase's exposed schemas in API settings.
revoke all on schema horde from public, anon, authenticated;
grant usage on schema horde to service_role;

revoke all on all tables in schema horde from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema horde to service_role;

revoke all on all sequences in schema horde from public, anon, authenticated;
grant usage, select, update on all sequences in schema horde to service_role;

revoke all on all routines in schema horde from public, anon, authenticated;
grant execute on all routines in schema horde to service_role;

alter default privileges in schema horde
  revoke all on tables from public, anon, authenticated;
alter default privileges in schema horde
  grant select, insert, update, delete on tables to service_role;
alter default privileges in schema horde
  revoke all on sequences from public, anon, authenticated;
alter default privileges in schema horde
  grant usage, select, update on sequences to service_role;
alter default privileges in schema horde
  revoke execute on routines from public, anon, authenticated;
alter default privileges in schema horde
  grant execute on routines to service_role;

revoke execute on function horde.claim_job(text, integer) from public, anon, authenticated;
revoke execute on function horde.recover_expired_jobs() from public, anon, authenticated;
grant execute on function horde.claim_job(text, integer) to service_role;
grant execute on function horde.recover_expired_jobs() to service_role;
