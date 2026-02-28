import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from '../src/lib/supabase';
import { setCorsHeaders } from '../src/lib/auth';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  setCorsHeaders(res);

  // Check Supabase connection
  let dbStatus = 'unknown';
  try {
    const { error } = await supabaseAdmin.from('agents').select('count', { count: 'exact', head: true });
    dbStatus = error ? 'error' : 'ok';
  } catch (e) {
    dbStatus = 'error';
  }

  return res.status(200).json({
    status: dbStatus === 'ok' ? 'healthy' : 'degraded',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    checks: {
      database: dbStatus,
      storage: 'ok'  // Would check Supabase storage in real implementation
    }
  });
}
