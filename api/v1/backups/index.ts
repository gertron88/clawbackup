import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from '../../lib/supabase';
import { authenticateAgent, setCorsHeaders, handleOptions, errorResponse, successResponse } from '../../lib/auth';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    return handleOptions(res);
  }

  setCorsHeaders(res);

  // Authenticate
  const agent = await authenticateAgent(req);
  if (!agent) {
    return errorResponse(res, 401, 'Invalid API key');
  }

  if (req.method === 'GET') {
    // List backups
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
      console.error('List backups error:', error);
      return errorResponse(res, 500, 'Failed to list backups');
    }

    return successResponse(res, {
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

  if (req.method === 'POST') {
    // Create backup metadata (actual upload goes to Supabase Storage directly)
    const { name, tags, size_bytes, content_hash } = req.body;

    if (!name || !size_bytes || !content_hash) {
      return errorResponse(res, 400, 'name, size_bytes, and content_hash required');
    }

    // Check quota
    if (agent.storage_used_gb + (size_bytes / (1024 * 1024 * 1024)) > agent.storage_quota_gb) {
      return errorResponse(res, 403, 'Storage quota exceeded');
    }

    // Generate backup ID
    const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
    const random = Math.random().toString(36).substring(2, 10);
    const backupId = `bak_${timestamp}_${random}`;

    // Storage path
    const storagePath = `agents/${agent.id}/backups/${backupId}.enc`;

    // Create backup record
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
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days
      })
      .select()
      .single();

    if (error) {
      console.error('Create backup error:', error);
      return errorResponse(res, 500, 'Failed to create backup record');
    }

    // Generate signed URL for upload
    const { data: uploadData, error: uploadError } = await supabaseAdmin
      .storage
      .from('backups')
      .createSignedUploadUrl(storagePath);

    if (uploadError) {
      console.error('Signed URL error:', uploadError);
      return errorResponse(res, 500, 'Failed to generate upload URL');
    }

    // Update storage usage
    await supabaseAdmin
      .from('agents')
      .update({ 
        storage_used_gb: agent.storage_used_gb + (size_bytes / (1024 * 1024 * 1024))
      })
      .eq('id', agent.id);

    return successResponse(res, {
      backup_id: backupId,
      name: backup.name,
      size_bytes: backup.size_bytes,
      content_hash: backup.content_hash,
      upload_url: uploadData.signedUrl,
      token: uploadData.token,
      expires_at: backup.expires_at,
      message: 'Use the upload_url to PUT your encrypted backup file'
    }, 201);
  }

  return errorResponse(res, 405, 'Method not allowed');
}
