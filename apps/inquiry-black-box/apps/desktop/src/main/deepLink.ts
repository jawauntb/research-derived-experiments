export const INQUIRY_DEEP_LINK_PROTOCOL = "inquiry-black-box";

export type InquiryDeepLink = {
  href: string;
  action: "pair" | "open";
  source?: string;
  challenge?: string;
};

export function parseInquiryDeepLink(value: string, protocol = INQUIRY_DEEP_LINK_PROTOCOL): InquiryDeepLink | null {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return null;
  }

  if (url.protocol !== `${protocol}:`) {
    return null;
  }

  const action = url.hostname === "pair" || url.pathname.replace(/^\/+/, "") === "pair" ? "pair" : "open";
  const source = url.searchParams.get("source") ?? undefined;
  const challenge = url.searchParams.get("challenge") ?? undefined;
  return {
    href: url.toString(),
    action,
    ...(source ? { source } : {}),
    ...(challenge ? { challenge } : {}),
  };
}

export function findInquiryDeepLinkArg(
  argv: readonly string[],
  protocol = INQUIRY_DEEP_LINK_PROTOCOL,
): InquiryDeepLink | null {
  for (const arg of argv) {
    const parsed = parseInquiryDeepLink(arg, protocol);
    if (parsed) {
      return parsed;
    }
  }
  return null;
}
