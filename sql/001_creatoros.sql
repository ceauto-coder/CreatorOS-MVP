-- CreatorOS MVP 1.1 schema
-- Run this whole file in Supabase SQL Editor.

create extension if not exists vector with schema extensions;

create table if not exists public.creatoros_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  external_user_id text not null,
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists creatoros_conversations_user_idx on public.creatoros_conversations(external_user_id, updated_at desc);

create table if not exists public.creatoros_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.creatoros_conversations(id) on delete cascade,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists creatoros_messages_conversation_idx on public.creatoros_messages(conversation_id, created_at);

create table if not exists public.creatoros_memories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  external_user_id text not null,
  content text not null,
  memory_type text not null default 'preference',
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536),
  fingerprint text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.creatoros_memories add column if not exists fingerprint text;
create unique index if not exists creatoros_memories_fingerprint_idx on public.creatoros_memories(external_user_id, fingerprint) where fingerprint is not null;
create index if not exists creatoros_memories_user_idx on public.creatoros_memories(external_user_id, created_at desc);
create index if not exists creatoros_memories_embedding_hnsw on public.creatoros_memories using hnsw (embedding vector_cosine_ops) where embedding is not null;

create or replace function public.match_creatoros_memories(query_embedding vector(1536), match_user_id text, match_count integer default 6, min_similarity double precision default 0.35)
returns table (id uuid, content text, memory_type text, metadata jsonb, similarity double precision)
language sql stable as $$
  select m.id, m.content, m.memory_type, m.metadata, 1 - (m.embedding <=> query_embedding) as similarity
  from public.creatoros_memories m
  where m.external_user_id = match_user_id and m.embedding is not null and 1 - (m.embedding <=> query_embedding) >= min_similarity
  order by m.embedding <=> query_embedding
  limit least(greatest(match_count, 1), 50);
$$;

create or replace function public.set_creatoros_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

drop trigger if exists creatoros_conversations_updated_at on public.creatoros_conversations;
create trigger creatoros_conversations_updated_at before update on public.creatoros_conversations for each row execute function public.set_creatoros_updated_at();

drop trigger if exists creatoros_memories_updated_at on public.creatoros_memories;
create trigger creatoros_memories_updated_at before update on public.creatoros_memories for each row execute function public.set_creatoros_updated_at();

alter table public.creatoros_conversations enable row level security;
alter table public.creatoros_messages enable row level security;
alter table public.creatoros_memories enable row level security;

-- Backend only: never expose the Supabase service-role key to the browser.
