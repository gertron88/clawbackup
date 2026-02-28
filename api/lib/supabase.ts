import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;

if (!supabaseUrl || !supabaseServiceKey) {
  throw new Error('Missing Supabase environment variables');
}

// Service role client for server-side operations
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Types
export interface Agent {
  id: string;
  agent_name: string;
  moltbook_username?: string;
  api_key_hash: string;
  email?: string;
  password_hash?: string;
  recovery_codes?: string[];
  tier: string;
  storage_quota_gb: number;
  storage_used_gb: number;
  created_at: string;
}

export interface Backup {
  id: string;
  backup_id: string;
  agent_id: string;
  name: string;
  size_bytes: number;
  content_hash: string;
  storage_bucket: string;
  storage_path: string;
  tags: string[];
  created_at: string;
  expires_at: string;
}
