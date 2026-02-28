import * as crypto from 'crypto';
import * as bcrypt from 'bcryptjs';

const SALT_ROUNDS = 12;

// Hash API key for storage
export function hashApiKey(apiKey: string): string {
  return crypto.createHash('sha256').update(apiKey).digest('hex');
}

// Hash password for human auth
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

// Verify password
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// Generate recovery codes
export function generateRecoveryCodes(count: number = 10): string[] {
  const codes: string[] = [];
  for (let i = 0; i < count; i++) {
    codes.push(
      Array.from({ length: 4 }, () => 
        Math.random().toString(36).substring(2, 6).toUpperCase()
      ).join('-')
    );
  }
  return codes;
}

// Hash recovery codes for storage
export function hashRecoveryCodes(codes: string[]): string[] {
  return codes.map(code => 
    crypto.createHash('sha256').update(code).digest('hex').substring(0, 16)
  );
}

// Verify recovery code
export function verifyRecoveryCode(provided: string, hashedCodes: string[]): boolean {
  const hashed = crypto.createHash('sha256').update(provided).digest('hex').substring(0, 16);
  return hashedCodes.includes(hashed);
}

// Generate unique backup ID
export function generateBackupId(): string {
  const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
  const random = crypto.randomBytes(4).toString('hex');
  return `bak_${timestamp}_${random}`;
}

// Calculate SHA-256 hash
export function calculateHash(data: Buffer): string {
  return crypto.createHash('sha256').update(data).digest('hex');
}
