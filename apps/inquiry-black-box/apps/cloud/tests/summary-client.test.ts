import { describe, expect, test } from "bun:test";
import { createSummaryClientFromEnv, geminiSessionSummaryModel, openAiSessionSummaryModel } from "../src/lib/summaryClient";

const redactedInput = {
  privacy_class: "redacted-sync",
  payload: {
    report_id: "session-interpretation:session-cloud-1",
    report_kind: "session_interpretation",
    subject_session_id: "session-cloud-1",
    marker_count: 2,
    theme_count: 1,
    open_loop_count: 1,
    next_action_count: 1,
    summary: "Redacted local session summary.",
    themes: [{ kind: "copied-passage", title: "Copied evidence", confidence: 0.8, marker_count: 1, evidence_count: 1 }],
    next_actions: [{ suggestion_kind: "follow-up", category: "open_loop", title: "Write follow-up", confidence: 0.7, evidence_count: 1 }],
    limitations: ["No raw text, screenshots, app names, or window titles included."],
    provenance: { input_report_id: "session-interpretation:session-cloud-1" },
  },
};

describe("cloud summary provider client", () => {
  test("uses OpenAI Responses API with redacted prompt input", async () => {
    let requestedUrl = "";
    let authorization = "";
    let postedBody = "";
    const client = createSummaryClientFromEnv(
      {
        OPENAI_API_KEY: "fixture-openai-key",
        OPENAI_SESSION_SUMMARY_MODEL: "gpt-test-summary",
      },
      {
        fetchImpl: async (url, init) => {
          requestedUrl = url;
          authorization = new Headers(init?.headers).get("authorization") ?? "";
          postedBody = String(init?.body ?? "");
          return new Response(JSON.stringify({ output_text: "OpenAI cloud summary." }), { status: 200 });
        },
      },
    );

    const result = await client?.summarizeSession({
      job_id: "job-1",
      user_id: "user-a",
      input: redactedInput,
      session_id: "session-cloud-1",
    });

    expect(result).toMatchObject({
      provider: "openai",
      model: "gpt-test-summary",
      text: "OpenAI cloud summary.",
    });
    expect(requestedUrl).toBe("https://api.openai.com/v1/responses");
    expect(authorization).toBe("Bearer fixture-openai-key");
    expect(postedBody).toContain("redacted-sync");
    expect(postedBody).not.toContain("Cursor");
    expect(postedBody).not.toContain("com.todesktop.230313mzl4w4u92");
  });

  test("uses provider-specific model defaults instead of generic session models", async () => {
    expect(openAiSessionSummaryModel({ SESSION_SUMMARY_MODEL: "redacted-session-summary" })).toBe("gpt-5.5");
    expect(openAiSessionSummaryModel({ SESSION_SUMMARY_MODEL: "gpt-4.1-mini" })).toBe("gpt-4.1-mini");
    expect(geminiSessionSummaryModel({ SESSION_SUMMARY_MODEL: "redacted-session-summary" })).toBe("gemini-2.5-flash");
    expect(geminiSessionSummaryModel({ SESSION_SUMMARY_MODEL: "gemini-3.5-flash" })).toBe("gemini-3.5-flash");
  });

  test("falls back to Gemini with the current summary model default", async () => {
    let requestedUrl = "";
    const client = createSummaryClientFromEnv(
      {
        GOOGLE_API_KEY: "fixture-google-key",
      },
      {
        fetchImpl: async (url) => {
          requestedUrl = url;
          return new Response(
            JSON.stringify({
              candidates: [{ content: { parts: [{ text: "Gemini cloud summary." }] } }],
            }),
            { status: 200 },
          );
        },
      },
    );

    const result = await client?.summarizeSession({
      job_id: "job-1",
      user_id: "user-a",
      input: redactedInput,
      session_id: "session-cloud-1",
    });

    expect(result).toMatchObject({
      provider: "gemini",
      model: "gemini-2.5-flash",
      text: "Gemini cloud summary.",
    });
    expect(requestedUrl).toBe("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent");
  });
});
