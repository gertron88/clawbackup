import { VercelRequest, VercelResponse } from '@vercel/node';
import { supabaseAdmin } from '../../_lib/supabase';
import { authenticateAgent, setCorsHeaders, handleOptions, errorResponse, successResponse } from '../../_lib/auth';

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

  const { id } = req.query;
  if (!id || typeof id !== 'string') {
    return errorResponse(res, 400, 'Backup ID required');
  }

  // Get backup
  const { data: backup, error } = await supabaseAdmin
    .from('backups')
    .select('*')
    .eq('backup_id', id)
    .eq('agent_id', agent.id)
    .is('deleted_at', null)
    .single();

  if (error || !backup) {
    return errorResponse(res, 404, 'Backup not found');
  }

  if (req.method === 'GET') {
    // Get metadata
    if (req.query.metadata === 'true') {
      return successResponse(res, {
        backup_id: backup.backup_id,
        name: backup.name,
        size_bytes: backup.size_bytes,
        content_hash: backup.content_hash,
        tags: backup.tags,
        created_at: backup.created_at,
        expires_at: backup.expires_at
      });
    }

    // Generate signed download URL
    const { data: downloadData, error: downloadError } = await supabaseAdmin
      .storage
      .from(backup.storage_bucket)
      .createSignedUrl(backup.storage_path, 60 * 5); // 5 minutes

    if (downloadError) {
      console.error('Download URL error:', downloadError);
      return errorResponse(res, 500, 'Failed to generate download URL');
    }

    return successResponse(res, {
      backup_id: backup.backup_id,
      name: backup.name,
      size_bytes: backup.size_bytes,
      content_hash: backup.content_hash,
      download_url: downloadData.signedUrl,
      expires_in: 300, // 5 minutes
      message: 'Download the encrypted file and decrypt locally with your password'
    });
  }

  if (req.method === 'DELETE') {
    // Soft delete backup
    await supabaseAdmin
      .from('backups')
      .update({ deleted_at: new Date().toISOString() })
      .eq('id', backup.id);

    // Update storage usage
    await supabaseAdmin
      .from('agents')
      .update({ 
        storage_used_gb: Math.max(0, agent.storage_used_gb - (backup.size_bytes / (1024 * 1024 * 1024)))
      })
      .eq('id', agent.id);

    // Note: Actual file deletion can happen async via cleanup job

    return successResponse(res, { 
      success: true, 
      message: 'Backup marked for deletion' 
    });
  }

  return errorResponse(res, 405, 'Method not allowed');
}
