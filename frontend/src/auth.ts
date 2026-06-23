// Auth helpers: session storage and HTTP calls for /api/auth/*.
//
// The frontend keeps the JWT in `localStorage` for personal mode (persists
// across reloads) and `sessionStorage` for demo mode (cleared when the tab
// is closed). The browser never sets cookies, so cross-origin CORS does
// not need `allow_credentials`.

const STORAGE_KEY = "expensy.session";

export type Mode = "personal" | "demo";

export type Session = {
  token: string;
  name: string | null;
  mode: Mode;
  expiresAt: number; // unix ms
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function modeEndpoint(mode: Mode): string {
  return `${API_BASE_URL}/api/chat/${mode}/stream`;
}

function storageFor(mode: Mode): Storage {
  return mode === "demo" ? window.sessionStorage : window.localStorage;
}

function read(mode: Mode): Session | null {
  try {
    const raw = storageFor(mode).getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Session;
    if (
      !parsed ||
      typeof parsed.token !== "string" ||
      typeof parsed.expiresAt !== "number" ||
      (parsed.mode !== "personal" && parsed.mode !== "demo")
    ) {
      return null;
    }
    if (parsed.mode !== mode) return null;
    if (parsed.expiresAt <= Date.now()) {
      storageFor(mode).removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function getStoredSession(mode: Mode): Session | null {
  return read(mode);
}

export function setStoredSession(session: Session): void {
  storageFor(session.mode).setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession(mode?: Mode): void {
  if (mode) {
    storageFor(mode).removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
  window.sessionStorage.removeItem(STORAGE_KEY);
}

export async function login(
  name: string | null,
  password: string | null,
  mode: Mode,
): Promise<Session> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, password, mode }),
  });
  if (!res.ok) {
    let detail = "No se pudo iniciar sesion";
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  const body = (await res.json()) as {
    token: string;
    name: string | null;
    mode: Mode;
    expires_at: string;
  };
  const session: Session = {
    token: body.token,
    name: body.name,
    mode: body.mode,
    expiresAt: Date.parse(body.expires_at),
  };
  setStoredSession(session);
  return session;
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST" });
  } catch {
    // best-effort
  }
  clearStoredSession();
}

export async function fetchMe(
  session: Session,
): Promise<{ name: string | null; mode: Mode; expiresAt: number } | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${session.token}` },
    });
    if (!res.ok) return null;
    const body = (await res.json()) as {
      name: string | null;
      mode: Mode;
      expires_at: string;
    };
    return {
      name: body.name,
      mode: body.mode,
      expiresAt: Date.parse(body.expires_at),
    };
  } catch {
    return null;
  }
}
