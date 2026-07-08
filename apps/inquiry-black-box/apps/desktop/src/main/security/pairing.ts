import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export type PairingTokenInput = {
  secret: string;
  issuedAtMs?: number;
  nonce?: string;
};

export type PairingTokenVerification = {
  valid: boolean;
  reason: string;
};

export type PairingChallengeStore = {
  approveChallenge: (challenge: string, nowMs?: number) => void;
  consumeChallenge: (challenge: string, nowMs?: number) => boolean;
};

export type VerifyPairingTokenInput = {
  secret: string;
  token: string;
  nowMs?: number;
  maxAgeMs?: number;
  maxFutureSkewMs?: number;
};

const defaultMaxAgeMs = 24 * 60 * 60 * 1000;
const defaultMaxFutureSkewMs = 60 * 1000;
const defaultChallengeMaxAgeMs = 60_000;

export function createPairingSecret(): string {
  return randomBytes(32).toString("base64url");
}

export function createPairingToken(input: PairingTokenInput): string {
  assertUsableSecret(input.secret);
  const issuedAtMs = input.issuedAtMs ?? Date.now();
  const nonce = input.nonce ?? randomBytes(16).toString("base64url");
  const unsigned = `${issuedAtMs}.${nonce}`;
  const signature = sign(unsigned, input.secret);

  return `${unsigned}.${signature}`;
}

export function verifyPairingToken(input: VerifyPairingTokenInput): PairingTokenVerification {
  assertUsableSecret(input.secret);
  const nowMs = input.nowMs ?? Date.now();
  const maxAgeMs = input.maxAgeMs ?? defaultMaxAgeMs;
  const maxFutureSkewMs = input.maxFutureSkewMs ?? defaultMaxFutureSkewMs;
  const parts = input.token.split(".");

  if (parts.length !== 3) {
    return { valid: false, reason: "token must contain issued-at, nonce, and signature" };
  }

  const [issuedAtRaw, nonce, signature] = parts;
  const issuedAtMs = Number(issuedAtRaw);

  if (!issuedAtRaw || !nonce || !signature || !Number.isFinite(issuedAtMs)) {
    return { valid: false, reason: "token is malformed" };
  }

  if (issuedAtMs > nowMs + maxFutureSkewMs) {
    return { valid: false, reason: "token was issued in the future" };
  }

  if (nowMs - issuedAtMs > maxAgeMs) {
    return { valid: false, reason: "token is expired" };
  }

  const expected = sign(`${issuedAtRaw}.${nonce}`, input.secret);
  if (!secureEqual(signature, expected)) {
    return { valid: false, reason: "token signature is invalid" };
  }

  return { valid: true, reason: "token accepted" };
}

export function createPairingChallengeStore(maxAgeMs = defaultChallengeMaxAgeMs): PairingChallengeStore {
  const approved = new Map<string, number>();

  return {
    approveChallenge(challenge, nowMs = Date.now()) {
      assertUsableChallenge(challenge);
      pruneExpiredChallenges(approved, nowMs, maxAgeMs);
      approved.set(challenge, nowMs);
    },
    consumeChallenge(challenge, nowMs = Date.now()) {
      if (!isUsableChallenge(challenge)) {
        return false;
      }

      const approvedAt = approved.get(challenge);
      if (approvedAt === undefined) {
        return false;
      }

      approved.delete(challenge);
      return nowMs - approvedAt <= maxAgeMs;
    },
  };
}

function assertUsableSecret(secret: string): void {
  if (secret.trim().length < 16) {
    throw new Error("pairing secret must be at least 16 characters");
  }
}

function assertUsableChallenge(challenge: string): void {
  if (!isUsableChallenge(challenge)) {
    throw new Error("pairing challenge must be a non-empty bounded string");
  }
}

function isUsableChallenge(challenge: string): boolean {
  return challenge.length >= 16 && challenge.length <= 200;
}

function pruneExpiredChallenges(approved: Map<string, number>, nowMs: number, maxAgeMs: number): void {
  for (const [challenge, approvedAt] of approved) {
    if (nowMs - approvedAt > maxAgeMs) {
      approved.delete(challenge);
    }
  }
}

function sign(value: string, secret: string): string {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

function secureEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);

  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}
