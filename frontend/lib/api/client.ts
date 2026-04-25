export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

export class ApiFetchError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiFetchError";
  }
}

async function errorMessageFromResponse(response: Response) {
  let message = `API request failed: ${response.status}`;
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      message = payload.detail;
    }
  } catch {
    // Keep the status-based message when the server does not return JSON.
  }
  return message;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new ApiFetchError(await errorMessageFromResponse(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiFetchBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      Accept: "application/zip",
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new ApiFetchError(await errorMessageFromResponse(response), response.status);
  }
  return await response.blob();
}

export async function apiSendBinary<T>(
  path: string,
  body: Blob | ArrayBuffer,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    method: "POST",
    ...init,
    body,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/zip",
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new ApiFetchError(await errorMessageFromResponse(response), response.status);
  }
  return (await response.json()) as T;
}

export async function apiFetchEventStream(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  return await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
}
