export function hashForTelemetry(value: string): string {
  let hash = 5381;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 33) ^ value.charCodeAt(index);
  }

  return `h_${(hash >>> 0).toString(36)}`;
}
