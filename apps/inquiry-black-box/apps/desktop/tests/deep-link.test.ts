import { describe, expect, test } from "bun:test";
import { findInquiryDeepLinkArg, parseInquiryDeepLink } from "../src/main/deepLink";

describe("desktop deep links", () => {
  test("parses native pairing URLs without carrying secrets", () => {
    expect(parseInquiryDeepLink("inquiry-black-box://pair?source=chrome-extension&challenge=pairing-challenge-fixture-123")).toEqual({
      href: "inquiry-black-box://pair?source=chrome-extension&challenge=pairing-challenge-fixture-123",
      action: "pair",
      source: "chrome-extension",
      challenge: "pairing-challenge-fixture-123",
    });
    expect(parseInquiryDeepLink("https://example.test/pair")).toBeNull();
  });

  test("finds the protocol URL in secondary-instance argv", () => {
    expect(
      findInquiryDeepLinkArg(["/Applications/Inquiry Black Box.app", "inquiry-black-box://pair"]),
    ).toMatchObject({
      action: "pair",
      href: "inquiry-black-box://pair",
    });
  });
});
