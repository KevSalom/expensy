import { useMemo, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import {
  AssistantRuntimeProvider,
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  AuiIf,
} from "@assistant-ui/react";
import { useAISDKRuntime } from "@assistant-ui/react-ai-sdk";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatMode = "personal" | "demo";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const chatRuntime: { mode: ChatMode; token: string } = {
  mode: "demo",
  token: "",
};

function modeEndpoint(mode: ChatMode): string {
  return `${API_BASE_URL}/api/chat/${mode}/stream`;
}

type ProgressPart = { type: string; text?: string; data?: { text?: string } };

function AssistantMessage({ message }: { message: unknown }) {
  const msg = message as {
    parts?: readonly ProgressPart[];
    status?: { type: string };
  };
  const parts = msg.parts ?? [];
  const hasText = parts.some((p) => p.type === "text" && p.text);
  const lastProgress = [...parts]
    .reverse()
    .find((p) => p.type === "data" && p.data?.text);
  const isRunning = msg.status?.type === "running";

  return (
    <MessagePrimitive.Root className="messageBubble assistant">
      <div className="messageHeader">
        <span className="messageRole">Expensy</span>
      </div>
      {hasText ? (
        <MessagePrimitive.Parts>
          {({ part }) => {
            if (part.type === "text") {
              return (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {(part as { text?: string }).text ?? ""}
                </ReactMarkdown>
              );
            }
            return null;
          }}
        </MessagePrimitive.Parts>
      ) : (
        isRunning &&
        lastProgress && (
          <span className="messageProgress">{lastProgress.data?.text}</span>
        )
      )}
    </MessagePrimitive.Root>
  );
}

function App() {
  const [mode, setMode] = useState<ChatMode>("demo");
  const [token, setToken] = useState("");
  const [configOpen, setConfigOpen] = useState(false);

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: modeEndpoint(mode),
        prepareSendMessagesRequest: ({ messages }) => {
          const lastMessage = messages[messages.length - 1];
          const text =
            lastMessage?.parts
              ?.filter((p) => p.type === "text")
              .map((p) => (p as { text?: string }).text ?? "")
              .join("") ?? "";
          return {
            api: modeEndpoint(chatRuntime.mode),
            headers: {
              Authorization: `Bearer ${chatRuntime.token.trim()}`,
            },
            body: { message: text },
          };
        },
      }),
    [mode],
  );

  const chat = useChat({ transport });
  const runtime = useAISDKRuntime(chat);

  const isStreaming = chat.status === "submitted" || chat.status === "streaming";
  const canSend = token.trim().length > 0 && !isStreaming;

  function handleModeChange(nextMode: ChatMode) {
    chatRuntime.mode = nextMode;
    setMode(nextMode);
    chat.clearError();
  }

  function handleTokenChange(nextToken: string) {
    chatRuntime.token = nextToken;
    setToken(nextToken);
  }

  function clearChat() {
    chat.stop();
    chat.setMessages([]);
    chat.clearError();
    setConfigOpen(false);
  }

  return (
    <main className="appShell">
      <section className="workspace">
        <aside className="controlRail" aria-label="Configuracion de Expensy">
          <div>
            <p className="eyebrow">Expensy</p>
            <h1>Gastos, en lenguaje natural.</h1>
          </div>

          <div className="modeSwitch" aria-label="Modo de datos">
            <button
              type="button"
              className={mode === "demo" ? "active" : ""}
              onClick={() => handleModeChange("demo")}
            >
              Demo
            </button>
            <button
              type="button"
              className={mode === "personal" ? "active" : ""}
              onClick={() => handleModeChange("personal")}
            >
              Personal
            </button>
          </div>

          <label className="tokenField">
            <span>Contraseña {mode === "demo" ? "demo" : "personal"}</span>
            <input
              type="password"
              value={token}
              placeholder={
                mode === "demo" ? "Contraseña demo" : "Contraseña personal"
              }
              onChange={(event) => handleTokenChange(event.target.value)}
            />
            <small>Usa la contraseña configurada para este modo.</small>
          </label>

          <button
            type="button"
            className="secondaryAction"
            onClick={clearChat}
          >
            Limpiar chat
          </button>
        </aside>

        <AssistantRuntimeProvider runtime={runtime}>
          <section className="chatPanel" aria-label="Chat de Expensy">
            <ThreadPrimitive.Root className="chatPanelInner">
              <ThreadPrimitive.Viewport className="messageList" autoScroll={true}>
                <AuiIf condition={(s) => s.thread.isEmpty}>
                  <div className="emptyState">
                    <p>
                      Prueba con "registra cafe 3 USD en comida" o "cuanto gaste
                      esta semana".
                    </p>
                  </div>
                </AuiIf>

                <ThreadPrimitive.Messages>
                  {({ message }) => {
                    if (message.role === "user") {
                      return (
                        <MessagePrimitive.Root className="messageBubble user">
                          <div className="messageHeader">
                            <span className="messageRole">Tu</span>
                          </div>
                          <MessagePrimitive.Parts>
                            {({ part }) => {
                              if (part.type === "text") {
                                return (
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {(part as { text?: string }).text ?? ""}
                                  </ReactMarkdown>
                                );
                              }
                              return null;
                            }}
                          </MessagePrimitive.Parts>
                        </MessagePrimitive.Root>
                      );
                    }
                    return <AssistantMessage message={message} />;
                  }}
                </ThreadPrimitive.Messages>
              </ThreadPrimitive.Viewport>

              {chat.error ? (
                <div className="errorBox" role="alert">
                  <span>{chat.error.message}</span>
                  <button type="button" onClick={chat.clearError}>
                    Cerrar
                  </button>
                </div>
              ) : null}

              <ComposerPrimitive.Root className="composer">
                <ComposerPrimitive.Input
                  placeholder="Escribe un gasto o una consulta..."
                  rows={2}
                />
                <div className="composerActions">
                  <button
                    type="button"
                    onClick={chat.stop}
                    disabled={!isStreaming}
                  >
                    Detener
                  </button>
                  <ComposerPrimitive.Send disabled={!canSend}>
                    Enviar
                  </ComposerPrimitive.Send>
                </div>
              </ComposerPrimitive.Root>
            </ThreadPrimitive.Root>

            <nav className="bottomNav" aria-label="Navegacion">
              <button type="button" className="active" aria-current="page">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Chat
              </button>
              <button type="button" onClick={() => setConfigOpen(true)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
                Config
              </button>
            </nav>
          </section>
        </AssistantRuntimeProvider>

        <div
          className={`configDrawerOverlay ${configOpen ? "open" : ""}`}
          onClick={() => setConfigOpen(false)}
        />
        <aside className={`configDrawer ${configOpen ? "open" : ""}`} aria-label="Configuracion">
          <div className="drawerHeader">
            <h2>Configuracion</h2>
            <button
              type="button"
              className="drawerClose"
              onClick={() => setConfigOpen(false)}
              aria-label="Cerrar"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="drawerContent">
            <div className="modeSwitch" aria-label="Modo de datos">
              <button
                type="button"
                className={mode === "demo" ? "active" : ""}
                onClick={() => handleModeChange("demo")}
              >
                Demo
              </button>
              <button
                type="button"
                className={mode === "personal" ? "active" : ""}
                onClick={() => handleModeChange("personal")}
              >
                Personal
              </button>
            </div>

            <label className="tokenField">
              <span>Contraseña {mode === "demo" ? "demo" : "personal"}</span>
              <input
                type="password"
                value={token}
                placeholder={
                  mode === "demo" ? "Contraseña demo" : "Contraseña personal"
                }
                onChange={(event) => handleTokenChange(event.target.value)}
              />
              <small>Usa la contraseña configurada para este modo.</small>
            </label>

            <button
              type="button"
              className="secondaryAction"
              onClick={clearChat}
            >
              Limpiar chat
            </button>
          </div>
        </aside>
      </section>
    </main>
  );
}

export default App;
