-- CBIO+ Home Visit Register: server setup for Supabase (PostgreSQL).
-- Paste the whole file into the Supabase SQL Editor and run it once.
-- It is safe to run again: it only creates what is missing and replaces the functions.
--
-- Design: the app never reads or writes tables directly. Every table has Row Level
-- Security switched on with no policies, so the public key cannot touch them. The app
-- calls the functions below, which check the worker's session and limit her to her own
-- households (a Care Group Volunteer), her Care Group (a CHW) or everything (administrator).

create extension if not exists pgcrypto with schema extensions;

create table if not exists public.cbio_workers (
  id           text primary key,
  role         text not null check (role in ('admin','chw','chv')),
  name         text not null,
  village      text,
  chw_id       text,            -- for a Care Group Volunteer: her CHW
  cg           int,             -- Care Group number
  code         text not null unique,   -- sign-in name
  pin_hash     text not null,
  fails        int  not null default 0,
  locked_until timestamptz,
  active       boolean not null default true,
  created_at   timestamptz not null default now()
);

create table if not exists public.cbio_sessions (
  token      uuid primary key default gen_random_uuid(),
  worker_id  text not null references public.cbio_workers(id),
  expires_at timestamptz not null default now() + interval '90 days'
);

create sequence if not exists public.cbio_seq;

create table if not exists public.cbio_records (
  id         text primary key,
  ty         text not null,           -- hh, w, c, v, r, d, cen
  cgv        text,                    -- Care Group Volunteer who owns the household
  chw        text,                    -- CHW for that Care Group
  body       jsonb not null,
  u          bigint not null default 0,   -- time of the last edit on the tablet (ms)
  seq        bigint not null default nextval('public.cbio_seq'),
  updated_by text,
  updated_at timestamptz not null default now()
);
create index if not exists cbio_records_seq on public.cbio_records(seq);
create index if not exists cbio_records_chw on public.cbio_records(chw);
create index if not exists cbio_records_cgv on public.cbio_records(cgv);

create table if not exists public.cbio_settings (
  key        text primary key,
  body       jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.cbio_workers  enable row level security;
alter table public.cbio_sessions enable row level security;
alter table public.cbio_records  enable row level security;
alter table public.cbio_settings enable row level security;
revoke all on public.cbio_workers, public.cbio_sessions, public.cbio_records, public.cbio_settings from anon, authenticated;

-- Internal: who is signed in with this token.
create or replace function public.cbio_me(p_token text)
returns public.cbio_workers language plpgsql security definer set search_path = public, extensions as $$
declare w public.cbio_workers;
begin
  select wk.* into w from public.cbio_sessions s join public.cbio_workers wk on wk.id = s.worker_id
   where s.token::text = p_token and s.expires_at > now() and wk.active;
  if not found then raise exception 'not_signed_in'; end if;
  return w;
end $$;

create or replace function public.cbio_worker_json(w public.cbio_workers, with_code boolean)
returns jsonb language sql immutable as $$
  select jsonb_build_object('id', w.id, 'role', w.role, 'name', w.name, 'village', w.village, 'chwId', w.chw_id, 'cg', w.cg)
         || case when with_code then jsonb_build_object('code', w.code) else '{}'::jsonb end
$$;

-- Sign in. Five wrong PINs lock the account for 15 minutes.
create or replace function public.cbio_login(p_code text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare w public.cbio_workers; t uuid;
begin
  select * into w from public.cbio_workers where code = lower(trim(p_code)) and active;
  if not found then return jsonb_build_object('ok', false, 'error', 'wrong_code_or_pin'); end if;
  if w.locked_until is not null and w.locked_until > now() then return jsonb_build_object('ok', false, 'error', 'locked'); end if;
  if w.pin_hash <> crypt(p_pin, w.pin_hash) then
    update public.cbio_workers
       set fails = case when locked_until is not null then 1 else fails + 1 end,
           locked_until = case when locked_until is null and fails + 1 >= 5 then now() + interval '15 minutes' else null end
     where id = w.id;
    return jsonb_build_object('ok', false, 'error', 'wrong_code_or_pin');
  end if;
  update public.cbio_workers set fails = 0, locked_until = null where id = w.id;
  delete from public.cbio_sessions where expires_at < now();
  insert into public.cbio_sessions(worker_id) values (w.id) returning token into t;
  return jsonb_build_object('ok', true, 'token', t::text, 'worker', public.cbio_worker_json(w, false));
end $$;

-- First use only: creates the administrator. Refuses once an administrator exists.
create or replace function public.cbio_bootstrap(p_name text, p_code text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
begin
  if exists (select 1 from public.cbio_workers where role = 'admin') then return jsonb_build_object('ok', false, 'error', 'already_set_up'); end if;
  if coalesce(length(p_pin), 0) < 6 or coalesce(length(trim(p_code)), 0) < 3 or coalesce(trim(p_name), '') = '' then return jsonb_build_object('ok', false, 'error', 'bad_input'); end if;
  insert into public.cbio_workers(id, role, name, code, pin_hash)
  values ('s_adm_' || substr(md5(random()::text || clock_timestamp()::text), 1, 8), 'admin', trim(p_name), lower(trim(p_code)), crypt(p_pin, gen_salt('bf')));
  return public.cbio_login(p_code, p_pin);
end $$;

create or replace function public.cbio_logout(p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
begin
  delete from public.cbio_sessions where token::text = p_token;
  return jsonb_build_object('ok', true);
end $$;

-- Workers the caller may see: the administrator sees all; a CHW sees herself and her
-- volunteers; a volunteer sees herself and her CHW.
create or replace function public.cbio_workers_list(p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  return coalesce((select jsonb_agg(public.cbio_worker_json(w, me.role = 'admin') order by w.cg, w.role desc, w.name)
    from public.cbio_workers w
   where w.active and w.role <> 'admin'
     and (me.role = 'admin' or w.id = me.id or w.chw_id = me.id or w.id = me.chw_id)), '[]'::jsonb);
end $$;

-- Administrator: add or change a worker. p_pin sets a new PIN; leave it empty to keep the old one.
create or replace function public.cbio_save_worker(p_token text, p_worker jsonb, p_pin text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; w public.cbio_workers; v_id text; v_role text; v_chw text; v_cg int;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' then return jsonb_build_object('ok', false, 'error', 'admin_only'); end if;
  v_id := p_worker->>'id'; v_role := p_worker->>'role'; v_chw := p_worker->>'chwId';
  if v_id is not null then
    select * into w from public.cbio_workers where id = v_id;
    if not found then return jsonb_build_object('ok', false, 'error', 'no_such_worker'); end if;
    update public.cbio_workers set
      name = coalesce(nullif(trim(p_worker->>'name'), ''), name),
      village = coalesce(p_worker->>'village', village),
      pin_hash = case when coalesce(p_pin, '') <> '' then crypt(p_pin, gen_salt('bf')) else pin_hash end,
      fails = case when coalesce(p_pin, '') <> '' then 0 else fails end,
      locked_until = case when coalesce(p_pin, '') <> '' then null else locked_until end
    where id = v_id returning * into w;
    if coalesce(p_pin, '') <> '' then delete from public.cbio_sessions where worker_id = v_id; end if;
    return jsonb_build_object('ok', true, 'worker', public.cbio_worker_json(w, true));
  end if;
  if v_role not in ('chw', 'chv') or coalesce(trim(p_worker->>'name'), '') = '' or coalesce(length(p_pin), 0) < 6
     or coalesce(length(trim(p_worker->>'code')), 0) < 3 then return jsonb_build_object('ok', false, 'error', 'bad_input'); end if;
  if v_role = 'chv' then
    select cg into v_cg from public.cbio_workers where id = v_chw and role = 'chw';
    if not found then return jsonb_build_object('ok', false, 'error', 'no_such_chw'); end if;
  else
    v_chw := null; select coalesce(max(cg), 0) + 1 into v_cg from public.cbio_workers;
  end if;
  begin
    insert into public.cbio_workers(id, role, name, village, chw_id, cg, code, pin_hash)
    values ('s_' || substr(md5(random()::text || clock_timestamp()::text), 1, 10), v_role, trim(p_worker->>'name'), p_worker->>'village', v_chw, v_cg,
            lower(trim(p_worker->>'code')), crypt(p_pin, gen_salt('bf'))) returning * into w;
  exception when unique_violation then return jsonb_build_object('ok', false, 'error', 'code_taken');
  end;
  return jsonb_build_object('ok', true, 'worker', public.cbio_worker_json(w, true));
end $$;

-- Send records from a tablet. A record is accepted only inside the caller's own scope,
-- and only if it is newer than the copy the server holds.
create or replace function public.cbio_push(p_token text, p_records jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; r jsonb; v_cgv text; v_chw text; n int := 0; k int := 0; c int;
begin
  me := public.cbio_me(p_token);
  for r in select * from jsonb_array_elements(p_records) loop
    v_cgv := r->>'cgv'; v_chw := r->>'chw';
    if me.role = 'chv' then
      if v_cgv is distinct from me.id then k := k + 1; continue; end if;
      v_chw := me.chw_id;
    elsif me.role = 'chw' then
      if not exists (select 1 from public.cbio_workers w where w.id = v_cgv and w.chw_id = me.id) then k := k + 1; continue; end if;
      v_chw := me.id;
    else
      select w.chw_id into v_chw from public.cbio_workers w where w.id = v_cgv;
    end if;
    if coalesce(r->>'id', '') = '' or r->>'ty' not in ('hh','w','c','v','r','d','cen') then k := k + 1; continue; end if;
    insert into public.cbio_records as t (id, ty, cgv, chw, body, u, updated_by)
    values (r->>'id', r->>'ty', v_cgv, v_chw, r->'body', coalesce((r->>'u')::bigint, 0), me.id)
    on conflict (id) do update
      set ty = excluded.ty, cgv = excluded.cgv, chw = excluded.chw, body = excluded.body, u = excluded.u,
          seq = nextval('public.cbio_seq'), updated_by = excluded.updated_by, updated_at = now()
      where t.u < excluded.u and (me.role = 'admin' or t.chw = me.id or t.cgv = me.id);
    get diagnostics c = row_count;
    if c > 0 then n := n + 1; else k := k + 1; end if;
  end loop;
  return jsonb_build_object('ok', true, 'saved', n, 'skipped', k);
end $$;

-- Fetch records changed since the caller's last sync, inside her scope.
create or replace function public.cbio_pull(p_token text, p_since bigint)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; out_ jsonb;
begin
  me := public.cbio_me(p_token);
  select jsonb_build_object('ok', true, 'seq', coalesce(max(q.seq), p_since), 'count', count(*),
           'records', coalesce(jsonb_agg(jsonb_build_object('ty', q.ty, 'body', q.body) order by q.seq), '[]'::jsonb))
    into out_
    from (select * from public.cbio_records t
           where t.seq > p_since
             and (me.role = 'admin' or (me.role = 'chw' and t.chw = me.id) or (me.role = 'chv' and t.cgv = me.id))
           order by t.seq limit 1000) q;
  return out_;
end $$;

create or replace function public.cbio_settings_get(p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  return (select body from public.cbio_settings where key = 'cfg');
end $$;

create or replace function public.cbio_settings_set(p_token text, p_body jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' then return jsonb_build_object('ok', false, 'error', 'admin_only'); end if;
  insert into public.cbio_settings(key, body) values ('cfg', p_body)
  on conflict (key) do update set body = excluded.body, updated_at = now();
  return jsonb_build_object('ok', true);
end $$;

-- Only these functions can be called with the public key.
revoke execute on function public.cbio_me(text) from public, anon, authenticated;
revoke execute on function public.cbio_worker_json(public.cbio_workers, boolean) from public, anon, authenticated;
revoke execute on function public.cbio_login(text, text), public.cbio_bootstrap(text, text, text), public.cbio_logout(text),
  public.cbio_workers_list(text), public.cbio_save_worker(text, jsonb, text), public.cbio_push(text, jsonb),
  public.cbio_pull(text, bigint), public.cbio_settings_get(text), public.cbio_settings_set(text, jsonb) from public;
grant usage on schema public to anon, authenticated;
grant execute on function public.cbio_login(text, text), public.cbio_bootstrap(text, text, text), public.cbio_logout(text),
  public.cbio_workers_list(text), public.cbio_save_worker(text, jsonb, text), public.cbio_push(text, jsonb),
  public.cbio_pull(text, bigint), public.cbio_settings_get(text), public.cbio_settings_set(text, jsonb) to anon, authenticated;

notify pgrst, 'reload schema';
