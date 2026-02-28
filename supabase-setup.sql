-- Supabase SQL Setup for ClawBackup
-- Run this in Supabase SQL Editor

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Agents table (both agent and human access)
create table agents (
    id uuid primary key default uuid_generate_v4(),
    agent_name text unique not null,
    moltbook_username text,
    
    -- Agent auth
    api_key_hash text unique not null,
    
    -- Human auth (for dashboard/recovery)
    email text,
    password_hash text,
    
    -- Recovery
    recovery_codes text[] default '{}',
    
    -- Limits
    tier text default 'free',
    storage_quota_gb float default 0.5,
    storage_used_gb float default 0,
    
    created_at timestamp with time zone default now()
);

-- Backups table
create table backups (
    id uuid primary key default uuid_generate_v4(),
    backup_id text unique not null,
    agent_id uuid references agents(id) on delete cascade,
    
    name text not null,
    size_bytes integer not null,
    content_hash text not null,
    
    -- Storage location in Supabase
    storage_bucket text default 'backups',
    storage_path text not null,
    
    tags text[] default '{}',
    created_at timestamp with time zone default now(),
    expires_at timestamp with time zone not null,
    
    -- For soft delete (grace period)
    deleted_at timestamp with time zone
);

-- Indexes for performance
create index idx_agents_api_key on agents(api_key_hash);
create index idx_agents_email on agents(email);
create index idx_backups_agent on backups(agent_id);
create index idx_backups_backup_id on backups(backup_id);
create index idx_backups_deleted on backups(deleted_at) where deleted_at is null;

-- Enable Row Level Security
alter table agents enable row level security;
alter table backups enable row level security;

-- Policies for agents (service role bypasses these)
create policy "Agents can view own data" on agents
    for select using (true);  -- Service role handles auth

create policy "Agents can update own data" on agents
    for update using (true);

create policy "Backups accessible to owner" on backups
    for all using (true);  -- Service role handles auth

-- Storage bucket setup (run after creating bucket)
-- Note: Create the 'backups' bucket manually in Supabase UI first

-- Cleanup function for expired backups
create or replace function cleanup_expired_backups()
returns void as $$
begin
    -- Mark expired backups as deleted
    update backups
    set deleted_at = now()
    where expires_at < now()
    and deleted_at is null;
end;
$$ language plpgsql;

-- Schedule cleanup (requires pg_cron extension or use external cron)
-- select cron.schedule('cleanup-backups', '0 0 * * *', 'select cleanup_expired_backups()');
