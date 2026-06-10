import { useEffect, useMemo, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useAISDKRuntime } from "@assistant-ui/react-ai-sdk";

import { ControlRail } from "./components/ControlRail";
import { ChatPanel } from "./components/ChatPanel";
import { BottomNav } from "./components/BottomNav";
import { ConfigDrawer } from "./components/ConfigDrawer";
import { LoginModal } from "./components/LoginModal";
import {
  clearStoredSession,
  fetchMe,
  getStoredSession,
  logout as logoutRequest,
  modeEndpoint,
  type Mode,
  type Session,
} from "./auth";

type AuthStatus = "unknown" | "anonymous" | "authenticated";

function App() {
  const [mode, setMode] = useState<Mode>("personal");
  const [session, setSession] = useState<Session | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus>("unknown");
  const [configOpen, setConfigOpen] = useState(false);

  // Keep the latest session reachable from the transport's
  // `prepareSendMessagesRequest` callback without forcing `useChat` to
  // remount on every token change.
  const sessionRef = useRef<Session | null>(null);
  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  // Bootstrap: read session from storage and validate it with /me.
  // Runs once on mount.
  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const candidates: Mode[] = ["personal", "demo"];
      let refreshed: Session | null = null;
      let matchedMode: Mode | null = null;

      for (const candidate of candidates) {
        const stored = getStoredSession(candidate);
        if (!stored) continue;
        const me = await fetchMe(stored);
        if (cancelled) return;
        if (!me || me.expiresAt <= Date.now()) {
          clearStoredSession(candidate);
          continue;
        }
        refreshed = {
          token: stored.token,
          name: me.name,
          mode: me.mode,
          expiresAt: me.expiresAt,
        };
        matchedMode = me.mode;
        break;
      }

      if (cancelled) return;
      if (refreshed && matchedMode) {
        sessionRef.current = refreshed;
        setSession(refreshed);
        setMode(matchedMode);
        setAuthStatus("authenticated");
      } else {
        sessionRef.current = null;
        setSession(null);
        setAuthStatus("anonymous");
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: modeEndpoint("personal"), // overridden per-request
        prepareSendMessagesRequest: ({ messages }) => {
          const lastMessage = messages[messages.length - 1];
          const text =
            lastMessage?.parts
              ?.filter((p) => p.type === "text")
              .map((p) => (p as { text?: string }).text ?? "")
              .join("") ?? "";
          const current = sessionRef.current;
          const targetMode: Mode = current?.mode ?? "personal";
          const headers: Record<string, string> = {};
          if (current?.token) {
            headers.Authorization = `Bearer ${current.token}`;
          }
          return {
            api: modeEndpoint(targetMode),
            headers,
            body: { message: text },
          };
        },
      }),
    [],
  );

  const chat = useChat({ transport });
  const runtime = useAISDKRuntime(chat);

  // 401 handling: only drop the session when the backend explicitly
  // returns a 401 status. We can't infer 401 from a generic error
  // message because a transient failure (CORS, network, validation)
  // could contain "sesion" in a Spanish error string and would falsely
  // log us out.
  useEffect(() => {
    if (chat.status !== "error" || !chat.error) return;
    const err = chat.error as { status?: number; statusCode?: number };
    const status = err.status ?? err.statusCode;
    if (status === 401) {
      clearStoredSession();
      sessionRef.current = null;
      setSession(null);
      setAuthStatus("anonymous");
    }
  }, [chat.status, chat.error]);

  const isStreaming =
    chat.status === "submitted" || chat.status === "streaming";
  const canSend = authStatus === "authenticated" && !isStreaming;

  function handleLoginSuccess(newSession: Session) {
    sessionRef.current = newSession;
    setSession(newSession);
    setMode(newSession.mode);
    setAuthStatus("authenticated");
    chat.clearError();
  }

  function switchMode(nextMode: Mode) {
    // Changing mode invalidates the current session. The modal will
    // re-open with the new mode preselected.
    clearStoredSession();
    sessionRef.current = null;
    setSession(null);
    setMode(nextMode);
    setAuthStatus("anonymous");
    chat.clearError();
  }

  async function handleLogout() {
    await logoutRequest();
    clearStoredSession();
    sessionRef.current = null;
    setSession(null);
    setAuthStatus("anonymous");
    setConfigOpen(false);
  }

  function clearChat() {
    chat.stop();
    chat.setMessages([]);
    chat.clearError();
    setConfigOpen(false);
  }

  const showLogin = authStatus === "anonymous";

  return (
    <main className="appShell">
      <section className="workspace">
        <ControlRail
          mode={mode}
          userName={session?.name ?? null}
          isAuthenticated={authStatus === "authenticated"}
          onSwitchMode={switchMode}
          onClearChat={clearChat}
          onLogout={handleLogout}
        />

        <AssistantRuntimeProvider runtime={runtime}>
          <ChatPanel
            error={chat.error ?? null}
            isStreaming={isStreaming}
            canSend={canSend}
            onClearError={chat.clearError}
            onStop={chat.stop}
          />
          <BottomNav onConfigClick={() => setConfigOpen(true)} />
        </AssistantRuntimeProvider>

        <ConfigDrawer
          open={configOpen}
          mode={mode}
          userName={session?.name ?? null}
          isAuthenticated={authStatus === "authenticated"}
          onSwitchMode={switchMode}
          onClose={() => setConfigOpen(false)}
          onClearChat={clearChat}
          onLogout={handleLogout}
        />
      </section>

      <LoginModal
        open={showLogin}
        initialMode={mode}
        onSuccess={handleLoginSuccess}
      />
    </main>
  );
}

export default App;
