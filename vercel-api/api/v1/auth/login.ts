import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from '../../_lib/supabase';
import { verifyPassword } from '../../_lib/crypto';
import { setCorsHeaders, handleOptions, errorResponse, successResponse } from '../../_lib/auth';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    return handleOptions(res);
  }

  setCorsHeaders(res);

  if (req.method !== 'POST') {
    return errorResponse(res, 405, 'Method not allowed');
  }

  const { email, password } = req.body;

  if (!email || !password) {
    return errorResponse(res, 400, 'Email and password required');
  }

  // Find agent by email
  const { data: agent, error } = await supabaseAdmin
    .from('agents')
    .select('*')
    .eq('email', email)
    .single();

  if (error || !agent || !agent.password_hash) {
    return errorResponse(res, 401, 'Invalid credentials');
  }

  // Verify password
  const valid = await verifyPassword(password, agent.password_hash);
  if (!valid) {
    return errorResponse(res, 401, 'Invalid credentials');
  }

  // Return session token (in production, use JWT)
  return successResponse(res, {
    agent_id: agent.id,
    agent_name: agent.agent_name,
    token: 'session_token_' + Date.now(),  // Use real JWT in production
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
  });
}
