import { VercelRequest, VercelResponse } from '@vercel/node';
import { authenticateAgent, setCorsHeaders, handleOptions, errorResponse, successResponse } from '../../../src/lib/auth';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    return handleOptions(res);
  }

  setCorsHeaders(res);

  if (req.method !== 'GET') {
    return errorResponse(res, 405, 'Method not allowed');
  }

  // Authenticate
  const agent = await authenticateAgent(req);
  if (!agent) {
    return errorResponse(res, 401, 'Invalid API key');
  }

  // Return agent info (without sensitive fields)
  return successResponse(res, {
    agent_id: agent.id,
    agent_name: agent.agent_name,
    moltbook_username: agent.moltbook_username,
    tier: agent.tier,
    storage_quota_gb: agent.storage_quota_gb,
    storage_used_gb: agent.storage_used_gb,
    created_at: agent.created_at
  });
}
