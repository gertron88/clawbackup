import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from '../_lib/supabase';
import { 
  hashApiKey, 
  hashPassword, 
  generateRecoveryCodes, 
  hashRecoveryCodes 
} from '../_lib/crypto';
import { 
  setCorsHeaders, 
  handleOptions, 
  errorResponse, 
  successResponse 
} from '../_lib/auth';

// Generate API key
function generateApiKey(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = 'cbak_live_';
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    return handleOptions(res);
  }

  setCorsHeaders(res);

  if (req.method !== 'POST') {
    return errorResponse(res, 405, 'Method not allowed');
  }

  const { agent_name, moltbook_username, email, password } = req.body;

  // Validate
  if (!agent_name || !/^[a-zA-Z0-9_-]{3,64}$/.test(agent_name)) {
    return errorResponse(res, 400, 'Invalid agent_name. Must be 3-64 alphanumeric characters.');
  }

  // Check if agent name exists
  const { data: existing } = await supabaseAdmin
    .from('agents')
    .select('id')
    .eq('agent_name', agent_name)
    .single();

  if (existing) {
    return errorResponse(res, 409, 'Agent name already registered');
  }

  // Generate credentials
  const apiKey = generateApiKey();
  const apiKeyHash = hashApiKey(apiKey);
  const recoveryCodes = generateRecoveryCodes(10);
  const hashedRecoveryCodes = hashRecoveryCodes(recoveryCodes);

  // Hash password if provided (for human dashboard access)
  let passwordHash = null;
  if (password) {
    passwordHash = await hashPassword(password);
  }

  // Create agent
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
      storage_quota_gb: 0.5,  // 500MB free tier
      storage_used_gb: 0
    })
    .select('id, agent_name, moltbook_username, tier, storage_quota_gb, storage_used_gb, created_at')
    .single();

  if (error) {
    console.error('Registration error:', error);
    return errorResponse(res, 500, 'Failed to create agent');
  }

  // Return agent info with API key (shown only once!)
  return successResponse(res, {
    agent_id: agent.id,
    agent_name: agent.agent_name,
    moltbook_username: agent.moltbook_username,
    tier: agent.tier,
    storage_quota_gb: agent.storage_quota_gb,
    storage_used_gb: agent.storage_used_gb,
    api_key: apiKey,  // SAVE THIS!
    recovery_codes: recoveryCodes,  // SAVE THESE TOO!
    created_at: agent.created_at,
    message: 'Save your API key and recovery codes! They will not be shown again.'
  }, 201);
}
