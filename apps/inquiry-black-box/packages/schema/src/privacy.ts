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

export const sensitivePayloadFieldNames = [
  "rawFrame",
  "frameImage",
  "imageBlob",
  "frameBlob",
  "pixels",
  "keyText",
  "keyContent",
  "documentText",
  "rawVideo",
  "videoBytes",
] as const;

const syncEligible = new Set<PrivacyClass>(["public", "redacted-sync"]);
const exportEligible = new Set<PrivacyClass>(["public", "local-derived", "redacted-sync", "document-opt-in"]);
const sensitivePayloadFields = new Set<string>(sensitivePayloadFieldNames);

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
  const present = findSensitiveFieldPaths(payload);

  if (present.length > 0) {
    throw new Error(`payload contains blocked sensitive field(s): ${present.join(", ")}`);
  }
}

export function findSensitiveFieldPaths(value: unknown, path = "$"): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => findSensitiveFieldPaths(item, `${path}[${index}]`));
  }

  if (typeof value !== "object" || value === null) {
    return [];
  }

  const paths: string[] = [];
  for (const [key, child] of Object.entries(value)) {
    const childPath = `${path}.${key}`;
    if (sensitivePayloadFields.has(key)) {
      paths.push(childPath);
    }
    paths.push(...findSensitiveFieldPaths(child, childPath));
  }

  return paths;
}
