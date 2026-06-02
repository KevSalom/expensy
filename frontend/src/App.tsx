import { useMemo, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useAISDKRuntime } from "@assistant-ui/react-ai-sdk";

import { ControlRail } from "./components/ControlRail";
import { ChatPanel } from "./components/ChatPanel";
import { BottomNav } from "./components/BottomNav";
import { ConfigDrawer } from "./components/ConfigDrawer";

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
        <ControlRail
          mode={mode}
          token={token}
          onModeChange={handleModeChange}
          onTokenChange={handleTokenChange}
          onClearChat={clearChat}
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
          token={token}
          onModeChange={handleModeChange}
          onTokenChange={handleTokenChange}
          onClose={() => setConfigOpen(false)}
          onClearChat={clearChat}
        />
      </section>
    </main>
  );
}

export default App;