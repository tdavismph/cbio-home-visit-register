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

-- Programmes: one partner's programme within this country database. Added in version 0.4; safe to re-run on an existing database.
create table if not exists public.cbio_programmes (
  id         text primary key,
  name       text not null,
  partner    text,
  country    text,
  created_at timestamptz not null default now()
);
alter table public.cbio_workers add column if not exists prog text;   -- programme; empty for the country administrator, who sees every programme
alter table public.cbio_records add column if not exists prog text;   -- programme of the household's worker
create index if not exists cbio_records_prog on public.cbio_records(prog);
alter table public.cbio_workers drop constraint if exists cbio_workers_role_check;
alter table public.cbio_workers add constraint cbio_workers_role_check check (role in ('admin','chw','chv','sup'));   -- sup = supervisor, who fills out QIVCs

alter table public.cbio_programmes enable row level security;
revoke all on public.cbio_programmes from anon, authenticated;
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
  select jsonb_build_object('id', w.id, 'role', w.role, 'name', w.name, 'village', w.village, 'chwId', w.chw_id, 'cg', w.cg, 'prog', w.prog)
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
     and ((me.role in ('admin','sup') and (me.prog is null or w.prog is not distinct from me.prog)) or w.id = me.id or w.chw_id = me.id or w.id = me.chw_id)), '[]'::jsonb);
end $$;

-- Administrator: add or change a worker. p_pin sets a new PIN; leave it empty to keep the old one.
create or replace function public.cbio_save_worker(p_token text, p_worker jsonb, p_pin text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; w public.cbio_workers; v_id text; v_role text; v_chw text; v_cg int; v_prog text;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' then return jsonb_build_object('ok', false, 'error', 'admin_only'); end if;
  v_id := p_worker->>'id'; v_role := p_worker->>'role'; v_chw := p_worker->>'chwId';
  v_prog := coalesce(me.prog, nullif(p_worker->>'prog', ''));   -- a programme administrator can only work inside her own programme
  if v_id is not null then
    select * into w from public.cbio_workers where id = v_id;
    if not found or (me.prog is not null and (w.prog is distinct from me.prog or w.role = 'admin')) then return jsonb_build_object('ok', false, 'error', 'no_such_worker'); end if;
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
  if v_role not in ('chw', 'chv', 'admin', 'sup') or coalesce(trim(p_worker->>'name'), '') = '' or coalesce(length(p_pin), 0) < 6
     or coalesce(length(trim(p_worker->>'code')), 0) < 3 then return jsonb_build_object('ok', false, 'error', 'bad_input'); end if;
  if v_prog is not null and not exists (select 1 from public.cbio_programmes where id = v_prog) then return jsonb_build_object('ok', false, 'error', 'no_such_programme'); end if;
  if v_role = 'admin' then   -- a programme administrator, created by the country administrator
    if me.prog is not null or v_prog is null then return jsonb_build_object('ok', false, 'error', 'country_admin_only'); end if;
    v_chw := null; v_cg := null;
  elsif v_role = 'sup' then   -- a supervisor: observes workers, fills out QIVCs and reads the programme's reports; cannot write household records
    v_chw := null; v_cg := null;
  elsif v_role = 'chv' then
    select cg, prog into v_cg, v_prog from public.cbio_workers where id = v_chw and role = 'chw' and (me.prog is null or prog is not distinct from me.prog);
    if not found then return jsonb_build_object('ok', false, 'error', 'no_such_chw'); end if;
  else
    v_chw := null; select coalesce(max(cg), 0) + 1 into v_cg from public.cbio_workers where prog is not distinct from v_prog;
  end if;
  begin
    insert into public.cbio_workers(id, role, name, village, chw_id, cg, code, pin_hash, prog)
    values ('s_' || substr(md5(random()::text || clock_timestamp()::text), 1, 10), v_role, trim(p_worker->>'name'), p_worker->>'village', v_chw, v_cg,
            lower(trim(p_worker->>'code')), crypt(p_pin, gen_salt('bf')), v_prog) returning * into w;
  exception when unique_violation then return jsonb_build_object('ok', false, 'error', 'code_taken');
  end;
  return jsonb_build_object('ok', true, 'worker', public.cbio_worker_json(w, true));
end $$;

-- Send records from a tablet. A record is accepted only inside the caller's own scope,
-- and only if it is newer than the copy the server holds.
create or replace function public.cbio_push(p_token text, p_records jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; r jsonb; v_cgv text; v_chw text; v_prog text; n int := 0; k int := 0; c int;
begin
  me := public.cbio_me(p_token);
  for r in select * from jsonb_array_elements(p_records) loop
    v_cgv := r->>'cgv'; v_chw := r->>'chw';
    if r->>'ty' = 'q' then   -- a QIVC: written by an administrator, a supervisor, or the CHW of the volunteer observed (never by the worker observed)
      if not (me.role in ('admin', 'sup') or (me.role = 'chw' and exists (select 1 from public.cbio_workers w where w.id = v_cgv and w.chw_id = me.id))) then k := k + 1; continue; end if;
      select coalesce(w.chw_id, w.id) into v_chw from public.cbio_workers w where w.id = v_cgv;
      if v_chw is null then k := k + 1; continue; end if;
    elsif me.role = 'sup' then k := k + 1; continue;   -- a supervisor writes nothing else
    elsif me.role = 'chv' then
      if v_cgv is distinct from me.id then k := k + 1; continue; end if;
      v_chw := me.chw_id;
    elsif me.role = 'chw' then
      if not exists (select 1 from public.cbio_workers w where w.id = v_cgv and (w.chw_id = me.id or w.id = me.id)) then k := k + 1; continue; end if;
      v_chw := me.id;
    else
      select coalesce(w.chw_id, w.id) into v_chw from public.cbio_workers w where w.id = v_cgv;
    end if;
    select w.prog into v_prog from public.cbio_workers w where w.id = v_cgv;
    if me.role in ('admin', 'sup') and me.prog is not null and v_prog is distinct from me.prog then k := k + 1; continue; end if;
    if coalesce(r->>'id', '') = '' or r->>'ty' not in ('hh','w','c','v','r','d','cen','q') then k := k + 1; continue; end if;
    insert into public.cbio_records as t (id, ty, cgv, chw, prog, body, u, updated_by)
    values (r->>'id', r->>'ty', v_cgv, v_chw, v_prog, r->'body', coalesce((r->>'u')::bigint, 0), me.id)
    on conflict (id) do update
      set ty = excluded.ty, cgv = excluded.cgv, chw = excluded.chw, prog = excluded.prog, body = excluded.body, u = excluded.u,
          seq = nextval('public.cbio_seq'), updated_by = excluded.updated_by, updated_at = now()
      where t.u < excluded.u and (t.ty = 'q') = (excluded.ty = 'q')
        and ((me.role = 'admin' and (me.prog is null or t.prog is not distinct from me.prog)) or (me.role = 'sup' and t.ty = 'q') or t.chw = me.id or (t.cgv = me.id and t.ty <> 'q'));
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
             and ((me.role = 'admin' and (me.prog is null or t.prog is not distinct from me.prog)) or (me.role = 'chw' and t.chw = me.id) or (me.role = 'chv' and t.cgv = me.id)
                  or (me.role = 'sup' and (me.prog is null or t.prog is not distinct from me.prog)))   -- a supervisor reads the programme's records for the Reports, and writes only QIVCs
           order by t.seq limit 1000) q;
  return out_;
end $$;

create or replace function public.cbio_settings_get(p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  -- a programme's own settings if it has saved any, otherwise the settings of the country database
  return coalesce((select body from public.cbio_settings where key = 'cfg:' || me.prog), (select body from public.cbio_settings where key = 'cfg'));
end $$;

create or replace function public.cbio_settings_set(p_token text, p_body jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' then return jsonb_build_object('ok', false, 'error', 'admin_only'); end if;
  insert into public.cbio_settings(key, body) values (case when me.prog is null then 'cfg' else 'cfg:' || me.prog end, p_body)
  on conflict (key) do update set body = excluded.body, updated_at = now();
  return jsonb_build_object('ok', true);
end $$;

-- Only these functions can be called with the public key.
-- ---------- programmes
create or replace function public.cbio_programmes_list(p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers;
begin
  me := public.cbio_me(p_token);
  return coalesce((select jsonb_agg(jsonb_build_object('id', p.id, 'name', p.name, 'partner', p.partner, 'country', p.country,
            'admins', case when me.role = 'admin' and me.prog is null then
               coalesce((select jsonb_agg(jsonb_build_object('id', a.id, 'name', a.name, 'code', a.code) order by a.name)
                           from public.cbio_workers a where a.role = 'admin' and a.prog = p.id and a.active), '[]'::jsonb) else '[]'::jsonb end) order by p.created_at)
    from public.cbio_programmes p where me.prog is null or p.id = me.prog), '[]'::jsonb);
end $$;

create or replace function public.cbio_save_programme(p_token text, p_programme jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; v_id text;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' or me.prog is not null then return jsonb_build_object('ok', false, 'error', 'country_admin_only'); end if;
  if coalesce(trim(p_programme->>'name'), '') = '' then return jsonb_build_object('ok', false, 'error', 'bad_input'); end if;
  v_id := coalesce(nullif(p_programme->>'id', ''), 'p_' || substr(md5(random()::text || clock_timestamp()::text), 1, 8));
  insert into public.cbio_programmes(id, name, partner, country) values (v_id, trim(p_programme->>'name'), p_programme->>'partner', p_programme->>'country')
  on conflict (id) do update set name = excluded.name, partner = excluded.partner, country = coalesce(excluded.country, public.cbio_programmes.country);
  return jsonb_build_object('ok', true, 'id', v_id);
end $$;

-- ---------- de-identified export, for the central IGHA database
-- Removes names, villages and free text; replaces every record number with a code that cannot be traced back;
-- moves all the dates of one household by the same number of days (between -14 and +14), so that ages and intervals stay exact.
create or replace function public.cbio_deid(j jsonb, salt text, shift int)
returns jsonb language plpgsql immutable as $$
declare k text; v jsonb; o jsonb := '{}'::jsonb; a jsonb := '[]'::jsonb;
begin
  if jsonb_typeof(j) = 'object' then
    for k, v in select * from jsonb_each(j) loop
      if k in ('name','head','village','mother','who','rel','narr','notes','dnote','belief','dx','tx','code','dirty','ex','pg','demo','byName','mtxt') then continue; end if;
      if k in ('id','hhId','mId','subj','chvId','chwId','by','wid') and jsonb_typeof(v) = 'string' then
        o := o || jsonb_build_object(k, substr(md5(salt || (v #>> '{}')), 1, 16));
      elsif jsonb_typeof(v) = 'string' and (v #>> '{}') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' then
        o := o || jsonb_build_object(k, to_char((v #>> '{}')::date + shift, 'YYYY-MM-DD'));
      elsif jsonb_typeof(v) in ('object', 'array') then
        o := o || jsonb_build_object(k, public.cbio_deid(v, salt, shift));
      else
        o := o || jsonb_build_object(k, v);
      end if;
    end loop;
    return o;
  elsif jsonb_typeof(j) = 'array' then
    for v in select * from jsonb_array_elements(j) loop
      a := a || jsonb_build_array(case when jsonb_typeof(v) in ('object', 'array') then public.cbio_deid(v, salt, shift) else v end);
    end loop;
    return a;
  end if;
  return j;
end $$;

create or replace function public.cbio_deid_export(p_token text, p_since bigint)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare me public.cbio_workers; v_salt text; out_ jsonb;
begin
  me := public.cbio_me(p_token);
  if me.role <> 'admin' or me.prog is not null then return jsonb_build_object('ok', false, 'error', 'country_admin_only'); end if;
  select body #>> '{}' into v_salt from public.cbio_settings where key = 'deid_salt';
  if v_salt is null then
    v_salt := md5(random()::text || clock_timestamp()::text) || md5(random()::text);
    insert into public.cbio_settings(key, body) values ('deid_salt', to_jsonb(v_salt));
  end if;
  select jsonb_build_object('ok', true, 'seq', coalesce(max(q.seq), p_since), 'count', count(*),
           'records', coalesce(jsonb_agg(jsonb_build_object('ty', q.ty, 'prog', q.prog, 'body', public.cbio_deid(q.body, v_salt, q.shift)) order by q.seq), '[]'::jsonb))
    into out_
    from (select t.*, (('x' || substr(md5(v_salt || coalesce(t.body->>'hhId', case when t.ty = 'hh' then t.id end,
                         (select p.body->>'hhId' from public.cbio_records p where p.id = t.body->>'subj'), t.id)), 1, 6))::bit(24)::int % 29) - 14 as shift
            from public.cbio_records t where t.seq > p_since order by t.seq limit 1000) q;
  return out_ || jsonb_build_object(
    'programmes', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'name', name, 'partner', partner, 'country', country)), '[]'::jsonb) from public.cbio_programmes),
    'workers', (select coalesce(jsonb_agg(jsonb_build_object('id', substr(md5(v_salt || w.id), 1, 16), 'role', w.role,
                  'chwId', case when w.chw_id is null then null else substr(md5(v_salt || w.chw_id), 1, 16) end, 'cg', w.cg, 'prog', w.prog)), '[]'::jsonb)
                  from public.cbio_workers w where w.role <> 'admin' and w.active));
end $$;

revoke execute on function public.cbio_me(text) from public, anon, authenticated;
revoke execute on function public.cbio_worker_json(public.cbio_workers, boolean) from public, anon, authenticated;
revoke execute on function public.cbio_deid(jsonb, text, int) from public, anon, authenticated;
revoke execute on function public.cbio_programmes_list(text), public.cbio_save_programme(text, jsonb), public.cbio_deid_export(text, bigint) from public;
grant execute on function public.cbio_programmes_list(text), public.cbio_save_programme(text, jsonb), public.cbio_deid_export(text, bigint) to anon, authenticated;
revoke execute on function public.cbio_login(text, text), public.cbio_bootstrap(text, text, text), public.cbio_logout(text),
  public.cbio_workers_list(text), public.cbio_save_worker(text, jsonb, text), public.cbio_push(text, jsonb),
  public.cbio_pull(text, bigint), public.cbio_settings_get(text), public.cbio_settings_set(text, jsonb) from public;
grant usage on schema public to anon, authenticated;
grant execute on function public.cbio_login(text, text), public.cbio_bootstrap(text, text, text), public.cbio_logout(text),
  public.cbio_workers_list(text), public.cbio_save_worker(text, jsonb, text), public.cbio_push(text, jsonb),
  public.cbio_pull(text, bigint), public.cbio_settings_get(text), public.cbio_settings_set(text, jsonb) to anon, authenticated;

notify pgrst, 'reload schema';
