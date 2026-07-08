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

export const privacySurfaces = [
  "default-export",
  "selected-text-opt-in-export",
  "cloud-sync",
  "modal-job",
  "delete-tombstone",
] as const;

export type PrivacySurface = (typeof privacySurfaces)[number];

export type PrivacyClassMatrix = Record<PrivacyClass, Record<PrivacySurface, PrivacyDecision>>;

export const sensitivePayloadFieldNames = [
  "rawFrame",
  "raw_frame",
  "frameImage",
  "frame_image",
  "imageBlob",
  "image_blob",
  "frameBlob",
  "frame_blob",
  "pixels",
  "rawPixels",
  "raw_pixels",
  "rawKey",
  "raw_key",
  "keyName",
  "key_name",
  "keyText",
  "key_text",
  "keyContent",
  "key_content",
  "pressedKey",
  "pressed_key",
  "typedText",
  "typed_text",
  "rawTypedText",
  "raw_typed_text",
  "inputText",
  "input_text",
  "inputValue",
  "input_value",
  "documentText",
  "document_text",
  "pageText",
  "page_text",
  "rawPageText",
  "raw_page_text",
  "bodyText",
  "body_text",
  "rawVideo",
  "raw_video",
  "videoBytes",
  "video_bytes",
] as const;

export const selectedTextPayloadFieldNames = [
  "selected_text",
  "selectedText",
  "selection_text",
  "selectionText",
  "copied_text",
  "copiedText",
  "highlight_text",
  "highlightText",
] as const;

export const rawTextPayloadFieldNames = ["text", "rawText", "content", "html", "markdown", "excerpt"] as const;

export type SensitiveFieldPathOptions = {
  extraFieldNames?: Iterable<string>;
  normalizeFieldName?: (fieldName: string) => string;
  path?: string;
};

export const privacyClassMatrix: PrivacyClassMatrix = {
  public: {
    "default-export": allow("public data is eligible for local export"),
    "selected-text-opt-in-export": deny("public data is not used for selected-text excerpts"),
    "cloud-sync": allow("public data is eligible for optional sync"),
    "modal-job": deny("Modal jobs require redacted-sync or explicit document-opt-in input"),
    "delete-tombstone": deny("cloud delete tombstones must use redacted-sync"),
  },
  "local-derived": {
    "default-export": allow("derived local metrics are eligible for local export"),
    "selected-text-opt-in-export": deny("local-derived events may include counts and hashes, not selected text"),
    "cloud-sync": deny("local-derived data stays local"),
    "modal-job": deny("local-derived data stays local unless converted to a redacted job input"),
    "delete-tombstone": deny("cloud delete tombstones must use redacted-sync"),
  },
  "redacted-sync": {
    "default-export": allow("redacted sync data is eligible for local export"),
    "selected-text-opt-in-export": deny("redacted-sync data must not carry selected text excerpts"),
    "cloud-sync": allow("redacted-sync data is eligible for optional sync"),
    "modal-job": allow("redacted-sync data is eligible for Modal jobs"),
    "delete-tombstone": allow("redacted-sync is the only privacy class for cloud delete tombstones"),
  },
  "document-opt-in": {
    "default-export": allow("document-opt-in data is eligible for local export"),
    "selected-text-opt-in-export": allow("selected text excerpts require document-opt-in"),
    "cloud-sync": deny("document-opt-in data is local/exportable but not sync eligible"),
    "modal-job": allow("explicit document-opt-in payloads may be submitted as Modal job inputs"),
    "delete-tombstone": deny("cloud delete tombstones must use redacted-sync"),
  },
  "debug-sensitive": {
    "default-export": deny("debug-sensitive data is omitted from default exports"),
    "selected-text-opt-in-export": deny("debug-sensitive data is not selected-text export data"),
    "cloud-sync": deny("debug-sensitive data cannot sync"),
    "modal-job": deny("debug-sensitive data cannot be sent to Modal"),
    "delete-tombstone": deny("debug-sensitive data cannot be used for tombstones"),
  },
  "blocked-sensitive": {
    "default-export": deny("blocked-sensitive data is never export eligible"),
    "selected-text-opt-in-export": deny("blocked-sensitive data is never selected-text export eligible"),
    "cloud-sync": deny("blocked-sensitive data cannot sync"),
    "modal-job": deny("blocked-sensitive data cannot be sent to Modal"),
    "delete-tombstone": deny("blocked-sensitive data cannot be used for tombstones"),
  },
};

export function isPrivacyClass(value: unknown): value is PrivacyClass {
  return typeof value === "string" && privacyClasses.includes(value as PrivacyClass);
}

export function isRetentionPolicy(value: unknown): value is RetentionPolicy {
  return typeof value === "string" && retentionPolicies.includes(value as RetentionPolicy);
}

export function canSyncPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  return privacyDecisionFor(privacyClass, "cloud-sync");
}

export function canExportPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  return privacyDecisionFor(privacyClass, "default-export");
}

export function canExportSelectedTextPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  return privacyDecisionFor(privacyClass, "selected-text-opt-in-export");
}

export function canRunModalJobPrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  return privacyDecisionFor(privacyClass, "modal-job");
}

export function canQueueDeleteTombstonePrivacyClass(privacyClass: PrivacyClass): PrivacyDecision {
  return privacyDecisionFor(privacyClass, "delete-tombstone");
}

export function privacyDecisionFor(privacyClass: PrivacyClass, surface: PrivacySurface): PrivacyDecision {
  return privacyClassMatrix[privacyClass][surface];
}

export function assertNoBlockedPayload(payload: Record<string, unknown>): void {
  const present = findSensitiveFieldPaths(payload);

  if (present.length > 0) {
    throw new Error(`payload contains blocked sensitive field(s): ${present.join(", ")}`);
  }
}

export function normalizeSensitiveFieldName(fieldName: string): string {
  return fieldName.replace(/[_-]/g, "").toLowerCase();
}

export function findSensitiveFieldPaths(value: unknown, options: SensitiveFieldPathOptions | string = {}): string[] {
  const resolvedOptions = typeof options === "string" ? { path: options } : options;
  const normalizeFieldName = resolvedOptions.normalizeFieldName ?? ((fieldName: string) => fieldName);
  const sensitiveFields = new Set(
    [...sensitivePayloadFieldNames, ...(resolvedOptions.extraFieldNames ?? [])].map(normalizeFieldName),
  );
  return findMatchingFieldPaths(value, sensitiveFields, normalizeFieldName, resolvedOptions.path ?? "$");
}

function findMatchingFieldPaths(
  value: unknown,
  sensitiveFields: Set<string>,
  normalizeFieldName: (fieldName: string) => string,
  path: string,
): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => findMatchingFieldPaths(item, sensitiveFields, normalizeFieldName, `${path}[${index}]`));
  }

  if (typeof value !== "object" || value === null) {
    return [];
  }

  const paths: string[] = [];
  for (const [key, child] of Object.entries(value)) {
    const childPath = `${path}.${key}`;
    if (sensitiveFields.has(normalizeFieldName(key))) {
      paths.push(childPath);
    }
    paths.push(...findMatchingFieldPaths(child, sensitiveFields, normalizeFieldName, childPath));
  }

  return paths;
}

function allow(reason: string): PrivacyDecision {
  return { allowed: true, reason };
}

function deny(reason: string): PrivacyDecision {
  return { allowed: false, reason };
}
