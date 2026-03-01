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

async function authenticateAgent(req: VercelRequest) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
  const apiKey = authHeader.substring(7);
  if (!apiKey.startsWith('cbak_')) return null;
  const apiKeyHash = hashApiKey(apiKey);
  const { data: agent } = await supabaseAdmin
    .from('agents')
    .select('*')
    .eq('api_key_hash', apiKeyHash)
    .single();
  return agent;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  setCorsHeaders(res);
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { pathname } = new URL(req.url || '/', 'http://localhost');

  // Health check
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

  // Register endpoint
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

  // Get agent info (me endpoint)
  if ((pathname === '/v1/auth/me' || pathname === '/api/v1/auth/me') && req.method === 'GET') {
    const agent = await authenticateAgent(req);
    if (!agent) {
      return res.status(401).json({ error: 'Invalid API key' });
    }
    return res.status(200).json({
      agent_id: agent.id,
      agent_name: agent.agent_name,
      moltbook_username: agent.moltbook_username,
      tier: agent.tier,
      storage_quota_gb: agent.storage_quota_gb,
      storage_used_gb: agent.storage_used_gb,
      created_at: agent.created_at
    });
  }

  // List backups
  if ((pathname === '/v1/backups' || pathname === '/api/v1/backups') && req.method === 'GET') {
    const agent = await authenticateAgent(req);
    if (!agent) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const offset = parseInt(req.query.offset as string) || 0;

    const { data: backups, error, count } = await supabaseAdmin
      .from('backups')
      .select('*', { count: 'exact' })
      .eq('agent_id', agent.id)
      .is('deleted_at', null)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      return res.status(500).json({ error: 'Failed to list backups' });
    }

    return res.status(200).json({
      backups: backups.map(b => ({
        backup_id: b.backup_id,
        name: b.name,
        size_bytes: b.size_bytes,
        content_hash: b.content_hash,
        tags: b.tags,
        created_at: b.created_at,
        expires_at: b.expires_at
      })),
      total: count,
      limit,
      offset
    });
  }

  // Create backup
  if ((pathname === '/v1/backups' || pathname === '/api/v1/backups') && req.method === 'POST') {
    const agent = await authenticateAgent(req);
    if (!agent) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    const { name, tags, size_bytes, content_hash } = req.body || {};

    if (!name || !size_bytes || !content_hash) {
      return res.status(400).json({ error: 'name, size_bytes, and content_hash required' });
    }

    if (agent.storage_used_gb + (size_bytes / (1024 * 1024 * 1024)) > agent.storage_quota_gb) {
      return res.status(403).json({ error: 'Storage quota exceeded' });
    }

    const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
    const random = Math.random().toString(36).substring(2, 10);
    const backupId = `bak_${timestamp}_${random}`;
    const storagePath = `agents/${agent.id}/backups/${backupId}.enc`;

    const { data: backup, error } = await supabaseAdmin
      .from('backups')
      .insert({
        backup_id: backupId,
        agent_id: agent.id,
        name,
        size_bytes,
        content_hash,
        storage_bucket: 'backups',
        storage_path: storagePath,
        tags: tags || [],
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
      })
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to create backup record' });
    }

    const { data: uploadData, error: uploadError } = await supabaseAdmin
      .storage
      .from('backups')
      .createSignedUploadUrl(storagePath);

    if (uploadError) {
      return res.status(500).json({ error: 'Failed to generate upload URL' });
    }

    await supabaseAdmin
      .from('agents')
      .update({ storage_used_gb: agent.storage_used_gb + (size_bytes / (1024 * 1024 * 1024)) })
      .eq('id', agent.id);

    return res.status(201).json({
      backup_id: backupId,
      name: backup.name,
      size_bytes: backup.size_bytes,
      content_hash: backup.content_hash,
      upload_url: uploadData.signedUrl,
      token: uploadData.token,
      expires_at: backup.expires_at,
      message: 'Use the upload_url to PUT your encrypted backup file'
    });
  }

  return res.status(404).json({ error: 'Not found', path: pathname });
}
