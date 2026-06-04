// In production, use same-origin requests (empty string) — Vercel rewrites
// proxy /api/v1/* to the backend, eliminating CORS entirely.
// In development, hit the local backend directly.
const isLocalDev =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export const API_BASE_URL = isLocalDev
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : '';

export const getApiUrl = (path: string) => {
  // Ensure path starts with /
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Parse a non-OK fetch Response and return the best human-readable message.
 * Handles both the legacy FastAPI shape (`{ detail: ... }`) and the new
 * envelope shape (`{ error: { code, message, request_id } }`) the hardened
 * backend uses.
 */
export async function extractErrorMessage(response: Response, fallback = 'Request failed'): Promise<string> {
  try {
    const data = await response.json();
    if (data && typeof data === 'object') {
      if (data.error && typeof data.error === 'object' && typeof data.error.message === 'string') {
        return data.error.message;
      }
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const first = data.detail[0];
        if (first && typeof first.msg === 'string') return first.msg;
      }
    }
  } catch {
    // Body wasn't JSON — fall through.
  }
  return fallback;
}

export async function fetchWithTimeout(resource: string, options: RequestInit & { timeout?: number } = {}) {
  const { timeout = 10000 } = options; // Default 10s timeout
  
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error: any) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please check if the backend is running and accessible.');
    }
    throw error;
  }
}

export interface ApiDocument {
  id: number;
  filename: string;
  blob_name: string;
  url: string | null;
  chunks_indexed: number | null;
  created_at: string | null;
}

/** Authoritative list of the user's uploaded reports (server-side, not localStorage). */
export async function listDocuments(token: string): Promise<ApiDocument[]> {
  const res = await fetchWithTimeout(getApiUrl('/api/v1/documents'), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res, 'Failed to load documents'));
  const data = await res.json();
  return Array.isArray(data?.documents) ? data.documents : [];
}

export async function analyzeInjury(file: File, token: string) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetchWithTimeout(getApiUrl('/api/v1/vision/analyze-injury'), {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
    timeout: 60000, // vision calls can take a while
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to analyze image'));
  }

  return response.json();
}

/** General medical-image analysis (report OR injury) — used by chat attachments. */
export async function analyzeImage(file: File, token: string) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetchWithTimeout(getApiUrl('/api/v1/vision/analyze'), {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
    timeout: 60000,
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to analyze image'));
  }

  return response.json();
}

export async function transcribeAudio(audioBlob: Blob, token: string) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');

  const response = await fetchWithTimeout(getApiUrl('/api/v1/speech/transcribe'), {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
    timeout: 60000, // transcription can take a while
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to transcribe audio'));
  }

  return response.json();
}
