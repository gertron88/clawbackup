import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from './supabase';
import { hashApiKey } from './crypto';

// CORS headers
export function setCorsHeaders(res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

// Handle OPTIONS requests
export function handleOptions(res: VercelResponse) {
  setCorsHeaders(res);
  res.status(200).end();
}

// Authenticate agent from API key
export async function authenticateAgent(req: VercelRequest) {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  
  const apiKey = authHeader.substring(7);
  if (!apiKey.startsWith('cbak_')) {
    return null;
  }
  
  const apiKeyHash = hashApiKey(apiKey);
  
  const { data: agent, error } = await supabaseAdmin
    .from('agents')
    .select('*')
    .eq('api_key_hash', apiKeyHash)
    .single();
  
  if (error || !agent) {
    return null;
  }
  
  return agent;
}

// Error response helper
export function errorResponse(res: VercelResponse, status: number, message: string) {
  setCorsHeaders(res);
  return res.status(status).json({ error: message });
}

// Success response helper
export function successResponse(res: VercelResponse, data: any, status: number = 200) {
  setCorsHeaders(res);
  return res.status(status).json(data);
}
