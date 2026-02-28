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

export default async function handler(req: VercelRequest, res: VercelResponse) {
  setCorsHeaders(res);
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { pathname } = new URL(req.url || '/', 'http://localhost');

  // Handle both /api/health and /health paths
  if (pathname === '/health' || pathname === '/' || pathname === '/api/health' || pathname === '/api/') {
    try {
      const { error } = await supabaseAdmin.from('agents').select('count', { count: 'exact', head: true });
      return res.status(200).json({
        status: error ? 'degraded' : 'healthy',
        version: '2.0.0',
        timestamp: new Date().toISOString()
      });
    } catch (e) {
      return res.status(200).json({ status: 'degraded', error: String(e) });
    }
  }

  // Register endpoint - handle both /api/v1/auth/register and /v1/auth/register
  if ((pathname === '/v1/auth/register' || pathname === '/api/v1/auth/register') && req.method === 'POST') {
    const { agent_name, moltbook_username, email, password } = req.body || {};

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
        recovery_codes: [],
        tier: 'free',
        storage_quota_gb: 0.5,
        storage_used_gb: 0
      })
      .select('id, agent_name, moltbook_username, tier, storage_quota_gb, storage_used_gb, created_at')
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to create agent', details: error.message });
    }

    return res.status(201).json({
      agent_id: agent.id,
      agent_name: agent.agent_name,
      api_key: apiKey,
      message: 'Save your API key!'
    });
  }

  return res.status(404).json({ error: 'Not found', path: pathname });
}
