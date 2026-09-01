const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    credentials: "include",
    cache: "no-store",
    ...init,
  });

  if (!response.ok) {
    let detail = `Erro ${response.status} ao acessar ${path}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Respostas sem JSON mantêm a mensagem padrão.
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function apiDelete<T = undefined>(path: string): Promise<T> {
  return apiRequest<T>(path, { method: "DELETE" });
}

export { API_BASE_URL };
