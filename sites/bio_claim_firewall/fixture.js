/* Shared receipt contract. This file contains no evidence and is safe to ship. */
(function attachFixtureApi(global) {
  const VOLATILE_FIELDS = new Set(["issued_at", "request_id", "parser_run"]);

  function canonicalize(value) {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.keys(value)
          .filter((key) => !VOLATILE_FIELDS.has(key))
          .sort()
          .map((key) => [key, canonicalize(value[key])]),
      );
    }
    return value;
  }

  function canonicalPayload(receipt) {
    const copy = { ...receipt };
    delete copy.canonical_digest;
    return JSON.stringify(canonicalize(copy));
  }

  async function digestReceipt(receipt) {
    if (!global.crypto || !global.crypto.subtle) return null;
    const bytes = new TextEncoder().encode(canonicalPayload(receipt));
    const digest = await global.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  const api = { canonicalize, canonicalPayload, digestReceipt, VOLATILE_FIELDS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (global) global.BioFirewallFixture = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
