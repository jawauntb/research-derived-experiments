import type { PrivacyClass } from "@inquiry/schema";

export type StimulusSource = "article" | "transcript" | "manual" | "pdf-text" | "video-note";

export type StimulusInput = {
  stimulus_id: string;
  source: StimulusSource;
  title?: string;
  text: string;
  content_ref?: string;
  document_opt_in?: boolean;
  evidence_event_ids?: string[];
  start_ms?: number;
  duration_ms?: number;
};

export type StimulusSegmentFeatures = {
  word_count: number;
  sentence_count: number;
  density: number;
  term_novelty: number;
  transition_count: number;
  quiz_checkpoint_candidate: boolean;
};

export type StimulusSegment = {
  segment_id: string;
  stimulus_id: string;
  source: StimulusSource;
  ordinal: number;
  start_ms: number;
  end_ms: number;
  content_ref: string;
  privacy_class: PrivacyClass;
  evidence_event_ids: string[];
  features: StimulusSegmentFeatures;
  evidence: string[];
  text?: string;
};

export type SegmentStimulusOptions = {
  target_words?: number;
  default_duration_ms?: number;
};

const stopWords = new Set([
  "about",
  "after",
  "again",
  "also",
  "because",
  "before",
  "being",
  "between",
  "could",
  "their",
  "there",
  "these",
  "those",
  "through",
  "under",
  "where",
  "which",
  "while",
  "would",
]);

const transitionWords = new Set([
  "although",
  "because",
  "but",
  "consequently",
  "however",
  "instead",
  "meanwhile",
  "therefore",
  "then",
  "thus",
  "whereas",
  "yet",
]);

const conceptPattern =
  /(baseline|causal|counterfactual|density|explanatory|phenomen|probabil|residual|stimulus|transition|triangulat|validat)/i;

export function segmentStimulus(input: StimulusInput, options: SegmentStimulusOptions = {}): StimulusSegment[] {
  if (input.stimulus_id.trim().length === 0) {
    throw new Error("stimulus_id must be non-empty");
  }

  const normalized = normalizeStimulusText(input.text);
  if (normalized.length === 0) {
    return [];
  }

  const targetWords = options.target_words ?? 72;
  const chunks = chunkText(normalized, targetWords);
  const durationMs = input.duration_ms ?? options.default_duration_ms ?? Math.max(30_000, chunks.length * 20_000);
  const startMs = input.start_ms ?? 0;
  const segmentDuration = durationMs / chunks.length;
  const contentRef = input.content_ref ?? `${input.source}:${input.stimulus_id}:${stableHash(normalized)}`;
  const privacyClass: PrivacyClass = input.document_opt_in === true ? "document-opt-in" : "local-derived";

  return chunks.map((chunk, index) => {
    const features = analyzeChunk(chunk);
    const segmentStart = Math.round(startMs + index * segmentDuration);
    const segmentEnd = Math.round(index === chunks.length - 1 ? startMs + durationMs : startMs + (index + 1) * segmentDuration);

    return {
      segment_id: `${input.stimulus_id}:${index + 1}`,
      stimulus_id: input.stimulus_id,
      source: input.source,
      ordinal: index + 1,
      start_ms: segmentStart,
      end_ms: segmentEnd,
      content_ref: `${contentRef}#${index + 1}`,
      privacy_class: privacyClass,
      evidence_event_ids: input.evidence_event_ids ?? [],
      features,
      evidence: [
        `density ${features.density.toFixed(2)}`,
        `term novelty ${features.term_novelty.toFixed(2)}`,
        `${features.transition_count} concept transition${features.transition_count === 1 ? "" : "s"}`,
      ],
      ...(input.document_opt_in === true ? { text: chunk } : {}),
    } satisfies StimulusSegment;
  });
}

function normalizeStimulusText(text: string): string {
  return text
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\r/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n[ \t]+/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function chunkText(text: string, targetWords: number): string[] {
  const paragraphs = text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  const units = paragraphs.length > 1 ? paragraphs : splitSentences(text);
  const chunks: string[] = [];
  let current: string[] = [];
  let currentWords = 0;

  for (const unit of units) {
    const wordCount = words(unit).length;
    if (current.length > 0 && currentWords + wordCount > targetWords) {
      chunks.push(current.join(" "));
      current = [];
      currentWords = 0;
    }

    current.push(unit);
    currentWords += wordCount;
  }

  if (current.length > 0) {
    chunks.push(current.join(" "));
  }

  return chunks.length > 0 ? chunks : [text];
}

function analyzeChunk(text: string): StimulusSegmentFeatures {
  const chunkWords = words(text);
  const sentenceCount = Math.max(1, splitSentences(text).length);
  const longTerms = new Set(chunkWords.filter((word) => word.length >= 7 && !stopWords.has(word)));
  const transitionCount = chunkWords.filter((word) => transitionWords.has(word) || conceptPattern.test(word)).length;
  const longWordRatio = chunkWords.length === 0 ? 0 : longTerms.size / chunkWords.length;
  const termNovelty = clamp(longWordRatio * 2.4);
  const averageSentenceWords = chunkWords.length / sentenceCount;
  const density = clamp(
    (averageSentenceWords / 26) * 0.28 +
      termNovelty * 0.42 +
      (transitionCount / 4) * 0.18 +
      longWordRatio * 0.12,
  );

  return {
    word_count: chunkWords.length,
    sentence_count: sentenceCount,
    density,
    term_novelty: termNovelty,
    transition_count: transitionCount,
    quiz_checkpoint_candidate: density >= 0.56 || transitionCount >= 2 || chunkWords.length >= 70,
  };
}

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

function words(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+(?:[-'][a-z0-9]+)?/g) ?? [];
}

function stableHash(text: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}
