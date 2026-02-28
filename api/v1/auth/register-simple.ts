import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@supabase/supabase-js';
import * as crypto from 'crypto';
import * as bcrypt from 'bcryptjs';

const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;
const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: { autoRefreshToken: false, persistSession: false }
});

function setCorsHeaders(res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

function hashApiKey(apiKey: string): string {
  return crypto.createHash('sha256').update(apiKey).digest('hex');
}

function generateApiKey(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = 'cbak_live_';
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

function generateRecoveryCodes(count: number = 10): string[] {
  const codes: string[] = [];
  for (let i = 0; i < count; i++) {
    codes.push(Array.from({ length: 4 }, () => 
      Math.random().toString(36).substring(2, 6).toUpperCase()
    ).join('-'));
  }
  return codes;
}

function hashRecoveryCodes(codes: string[]): string[] {
  return codes.map(code => 
    crypto.createHash('sha256').update(code).digest('hex').substring(0, 16)
  );
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  setCorsHeaders(res);
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { agent_name, moltbook_username, email, password } = req.body;

  if (!agent_name || !/^[a-zA-Z0-9_-]{3,64}$/.test(agent_name)) {
    return res.status(400).json({ error: 'Invalid agent_name' });
  }

  const { data: existing } = await supabaseAdmin
    .from('agents')
    .select('id')
    .eq('agent_name', agent_name)
    .single();

  if (existing) {
    return res.status(409).json({ error: 'Agent name already registered' });
  }

  const apiKey = generateApiKey();
  const apiKeyHash = hashApiKey(apiKey);
  const recoveryCodes = generateRecoveryCodes(10);
  const hashedRecoveryCodes = hashRecoveryCodes(recoveryCodes);

  let passwordHash = null;
  if (password) {
    passwordHash = await bcrypt.hash(password, 12);
  }

  const { data: agent, error } = await supabaseAdmin
    .from('agents')
    .insert({
      agent_name,
      moltbook_username: moltbook_username || null,
      email: email || null,
      api_key_hash: apiKeyHash,
      password_hash: passwordHash,
      recovery_codes: hashedRecoveryCodes,
      tier: 'free',
      storage_quota_gb: 0.5,
      storage_used_gb: 0
    })
    .select('id, agent_name, moltbook_username, tier, storage_quota_gb, storage_used_gb, created_at')
    .single();

  if (error) {
    return res.status(500).json({ error: 'Failed to create agent' });
  }

  return res.status(201).json({
    agent_id: agent.id,
    agent_name: agent.agent_name,
    api_key: apiKey,
    recovery_codes: recoveryCodes,
    message: 'Save your API key and recovery codes!'
  });
}
