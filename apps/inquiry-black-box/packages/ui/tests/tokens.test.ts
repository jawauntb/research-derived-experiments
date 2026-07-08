import { describe, expect, test } from "bun:test";
import {
  designTokens,
  inquiryCssVariableBlock,
  inquiryCssVariables,
  inquiryDarkCssVariableBlock,
  inquiryDarkCssVariables,
} from "../src/index";

describe("inquiry design tokens", () => {
  test("uses warm paper neutrals and teal signature accents", () => {
    expect(designTokens.surface).toBe("#f3f1eb");
    expect(designTokens.teal).toBe("#087d73");
    expect(designTokens.tealBright).toBe("#0f6b55");
  });

  test("exports css variables for desktop and popup surfaces", () => {
    const variables = inquiryCssVariables();
    expect(variables["--surface"]).toBe(designTokens.surface);
    expect(variables["--green"]).toBe(designTokens.tealBright);
    expect(inquiryCssVariableBlock(":root")).toContain("--surface: #f3f1eb;");
  });

  test("exports dark css variables for signed desktop and popup builds", () => {
    const variables = inquiryDarkCssVariables();
    expect(variables["--surface"]).toBe(designTokens.dark.surface);
    expect(variables["--green"]).toBe(designTokens.dark.tealBright);
    expect(inquiryDarkCssVariableBlock('[data-theme="dark"]')).toContain("--surface: #151816;");
  });
});
