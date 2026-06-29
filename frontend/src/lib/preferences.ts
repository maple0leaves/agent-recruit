export interface LocalPreferences {
  reviewThreshold: number;
  resumePreviewMode: "pdf" | "text";
  notifyPendingReview: boolean;
  matchCandidateLimit: number;
}

export const DEFAULT_PREFERENCES: LocalPreferences = {
  reviewThreshold: 70,
  resumePreviewMode: "pdf",
  notifyPendingReview: true,
  matchCandidateLimit: 5,
};

export const PREFERENCES_KEY = "agent-recruit-settings";

export function clampMatchCandidateLimit(value: number) {
  return Math.max(1, Math.min(30, Math.floor(value) || DEFAULT_PREFERENCES.matchCandidateLimit));
}

export function normalizePreferences(value: Partial<LocalPreferences> = {}): LocalPreferences {
  return {
    reviewThreshold: Math.max(0, Math.min(100, Number(value.reviewThreshold ?? DEFAULT_PREFERENCES.reviewThreshold))),
    matchCandidateLimit: clampMatchCandidateLimit(
      Number(value.matchCandidateLimit ?? DEFAULT_PREFERENCES.matchCandidateLimit),
    ),
    resumePreviewMode: value.resumePreviewMode === "text" ? "text" : "pdf",
    notifyPendingReview: value.notifyPendingReview ?? DEFAULT_PREFERENCES.notifyPendingReview,
  };
}

export function readPreferences(): LocalPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_PREFERENCES;
  }

  try {
    const raw = window.localStorage.getItem(PREFERENCES_KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    return normalizePreferences(JSON.parse(raw));
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function writePreferences(preferences: LocalPreferences) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(PREFERENCES_KEY, JSON.stringify(normalizePreferences(preferences)));
}
