const REQUEST_TIMEOUT_MS = 60000;
const API_BASE = import.meta.env.VITE_API_URL;

/**
 * Generic JSON API request helper.
 */
export async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      body: options.body,
      signal: controller.signal,
    });

    if (response.status === 429) {
      return { status: "error", message: "Too many requests. Please wait a moment." };
    }

    const data = await response.json();
    if (!response.ok && !data.status) {
      return { status: "error", message: data.message || "Server error." };
    }
    return data;
  } catch (err) {
    return { status: "error", message: "Could not reach the server. Please try again." };
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Single API entry point for Bloom.
 * Returns a structured result object; never throws to the caller.
 * @param {File} file - the user-selected image
 * @param {{signal?: AbortSignal}} options - optional external cancellation
 * @returns {Promise<object>} success | quality_error | face_error | invalid_image |
 *                            timeout | aborted | error
 */
export async function analyseImage(file, { signal } = {}) {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  const onExternalAbort = () => controller.abort();
  signal?.addEventListener("abort", onExternalAbort);

  try {
    const response = await fetch(`${API_BASE}/api/analyse`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    // rate limited
    if (response.status === 429) {
      return { status: "error", message: "Too many requests. Please wait a moment." };
    }

    const data = await response.json();
    if (!response.ok && !data.status) {
      return { status: "error", message: data.message || "Server error." };
    }
    return data;
  } catch (err) {
    if (timedOut) {
      return { status: "timeout", message: "The analysis timed out. Please try again." };
    }
    if (signal?.aborted || controller.signal.aborted) {
      return { status: "aborted", message: "Request cancelled." };
    }
    // network failure, CORS, or JSON parse failure
    return { status: "error", message: "Could not reach the server. Please try again." };
  } finally {
    clearTimeout(timeoutId);
    signal?.removeEventListener("abort", onExternalAbort);
  }
}
