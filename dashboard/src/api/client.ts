const API_BASE = import.meta.env.VITE_API_URL || '';

function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws/events`;
}

export const WS_URL = getWsUrl();

// Global project context — set by ProjectContext, read by apiFetch
let currentProjectPath: string | null = null;

export function setCurrentProjectPath(path: string | null) {
  currentProjectPath = path;
}

export function getCurrentProjectPath(): string | null {
  return currentProjectPath;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const projectHeaders: Record<string, string> = currentProjectPath
    ? { 'X-Project-Dir': currentProjectPath }
    : {};

  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...projectHeaders, ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || error.error || 'API request failed');
  }
  return res.json();
}
