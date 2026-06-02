import { ThreadPrimitive, AuiIf } from "@assistant-ui/react";
import { AssistantMessage } from "./AssistantMessage";
import { UserMessage } from "./UserMessage";
import { Composer } from "./Composer";

type Props = {
  error: { message: string } | null;
  isStreaming: boolean;
  canSend: boolean;
  onClearError: () => void;
  onStop: () => void;
};

export function ChatPanel({ error, isStreaming, canSend, onClearError, onStop }: Props) {
  return (
    <section className="chatPanel" aria-label="Chat de Expensy">
      <ThreadPrimitive.Root className="chatPanelInner">
        <ThreadPrimitive.Viewport className="messageList" autoScroll={true}>
          <AuiIf condition={(s) => s.thread.isEmpty}>
            <div className="emptyState">
              <p>
                <span className="emptyStatePrompt">Tengamos tus finanzas al día.</span>
                {" "}
                <span className="emptyStateQuestion">¿Qué quieres hacer hoy?</span>
              </p>
            </div>
          </AuiIf>

          <ThreadPrimitive.Messages>
            {({ message }) => {
              if (message.role === "user") {
                return <UserMessage/>;
              }
              return <AssistantMessage message={message} />;
            }}
          </ThreadPrimitive.Messages>
        </ThreadPrimitive.Viewport>

        {error ? (
          <div className="errorBox" role="alert">
            <span>{error.message}</span>
            <button type="button" onClick={onClearError}>
              Cerrar
            </button>
          </div>
        ) : null}

        <Composer isStreaming={isStreaming} canSend={canSend} onStop={onStop} />
      </ThreadPrimitive.Root>
    </section>
  );
}