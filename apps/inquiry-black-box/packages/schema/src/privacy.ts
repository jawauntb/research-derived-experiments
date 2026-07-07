export const privacyClasses = [
  "public",
  "local-derived",
  "redacted-sync",
  "document-opt-in",
  "debug-sensitive",
  "blocked-sensitive",
] as const;

export type PrivacyClass = (typeof privacyClasses)[number];

export const retentionPolicies = [
  "session-delete",
  "local-default",
  "expire-30d",
  "debug-ephemeral",
  "cloud-redacted",
] as const;

export type RetentionPolicy = (typeof retentionPolicies)[number];

export type PrivacyDecision = {
  allowed: boolean;
  reason: string;
};

const syncEligible = new Set<PrivacyClass>(["public", "redacted-sync"]);
const exportEligible = new Set<PrivacyClass>(["public", "local-derived", "redacted-sync", "document-opt-in"]);

export function isPrivacyClass(value: unknown): value is PrivacyClass {
  return typeof value === "string" && privacyClasses.includes(value as PrivacyClass);
}

export function isRetentionPolicy(value: unknown): value is RetentionPolicy {
  return typeof value === "string" && retentionPolicies.includes(value as RetentionPolicy);
}

export function canSyncPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  if (syncEligible.has(privacyClass)) {
    return { allowed: true, reason: "privacy class is eligible for optional sync" };
  }

  return {
    allowed: false,
    reason: `${privacyClass} requires local-only handling or explicit document/debug opt-in`,
  };
}

export function canExportPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  if (exportEligible.has(privacyClass)) {
    return { allowed: true, reason: "privacy class is eligible for local export" };
  }

  return {
    allowed: false,
    reason: `${privacyClass} is omitted from default exports`,
  };
}

export function assertNoBlockedPayload(payload: Record<string, unknown>): void {
  const forbiddenKeys = ["rawFrame", "frameImage", "keyText", "documentText"];
  const present = forbiddenKeys.filter((key) => key in payload);

  if (present.length > 0) {
    throw new Error(`payload contains blocked sensitive field(s): ${present.join(", ")}`);
  }
}
