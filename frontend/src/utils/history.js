const STORAGE_KEY = "bloom_scan_history";
const MAX_HISTORY = 5;

/** Save a scan result to localStorage history. */
export function saveScan(result) {
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const entry = {
      date: new Date().toISOString(),
      concerns: result.concerns,
      images: {
        improved_annotated: result.images?.improved_annotated || null,
      },
      processing_time_sec: result.processing_time_sec,
    };
    const updated = [entry, ...existing].slice(0, MAX_HISTORY);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.warn("Failed to save scan history:", e);
  }
}

/** Get scan history from localStorage (most recent first). */
export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch (e) {
    console.warn("Failed to read scan history:", e);
    return [];
  }
}

/** Clear all history. */
export function clearHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn("Failed to clear history:", e);
  }
}