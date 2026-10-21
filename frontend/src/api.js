/**
 * Single API entry point for Bloom.
 * Returns a structured result object; never throws to the caller.
 * @param {File} file - the user-selected image
 * @returns {Promise<object>} one of: success | quality_error | error shape
 */
export async function analyseImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/analyse`, {
      method: "POST",
      body: formData,
    });

    // rate limited
    if (response.status === 429) {
      return { status: "error", message: "Too many requests. Please wait a moment." };
    }

    const data = await response.json();
    // our backend sends status for success/quality_error; only fall back for HTML/other errors
    if (!response.ok && !data.status) {
      return { status: "error", message: data.message || "Server error." };
    }
    return data;
  } catch (err) {
    // network failure, CORS, JSON parse failure
    return { status: "error", message: "Could not reach the server. Please try again." };
  }
}
