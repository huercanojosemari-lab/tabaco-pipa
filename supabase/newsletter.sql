-- Pipateka · Newsletter
-- Ejecutar una sola vez en Supabase > SQL Editor.

create table if not exists public.newsletter_subscribers (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  name text,
  frequency text not null default 'Solo novedades importantes',
  consent boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.newsletter_subscribers enable row level security;

grant insert on public.newsletter_subscribers to anon, authenticated;

grant select, update, delete on public.newsletter_subscribers to authenticated;

drop policy if exists "newsletter_public_insert" on public.newsletter_subscribers;
create policy "newsletter_public_insert"
on public.newsletter_subscribers
for insert
to anon, authenticated
with check (
  consent = true
  and length(trim(email)) >= 5
  and length(trim(email)) <= 254
  and (frequency in ('Solo novedades importantes', 'Resumen mensual', 'Novedades cuando se publiquen'))
);

drop policy if exists "newsletter_own_read" on public.newsletter_subscribers;
create policy "newsletter_own_read"
on public.newsletter_subscribers
for select
to authenticated
using (email = (select auth.jwt()->>'email'));
