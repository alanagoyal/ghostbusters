-- A short server-timed lease; no camera data or device identity is exposed.
create table if not exists public.detector_heartbeats (
    session_id uuid primary key,
    last_seen timestamptz not null default now()
);
alter table public.detector_heartbeats enable row level security;
revoke all on public.detector_heartbeats from anon, authenticated;

create or replace function public.report_detector_heartbeat(session_id uuid, running boolean)
returns void language plpgsql security definer set search_path = '' as $$
begin
    delete from public.detector_heartbeats where last_seen < now() - interval '1 day';
    if running then
        insert into public.detector_heartbeats values (session_id, now())
        on conflict on constraint detector_heartbeats_pkey do update set last_seen = now();
    else
        delete from public.detector_heartbeats h where h.session_id = report_detector_heartbeat.session_id;
    end if;
end;
$$;
revoke all on function public.report_detector_heartbeat(uuid, boolean) from public, anon, authenticated;
grant execute on function public.report_detector_heartbeat(uuid, boolean) to service_role;

-- Only this aggregate boolean is public, never the underlying rows.
create or replace function public.detector_is_running()
returns boolean language sql stable security definer set search_path = '' as $$
    select exists(select 1 from public.detector_heartbeats
                  where last_seen > now() - interval '45 seconds');
$$;
revoke all on function public.detector_is_running() from public;
grant execute on function public.detector_is_running() to anon, authenticated, service_role;
