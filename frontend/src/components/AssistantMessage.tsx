import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessagePrimitive } from "@assistant-ui/react";

type ProgressPart = { type: string; text?: string; data?: { text?: string } };

type Props = {
  message: unknown;
};

export function AssistantMessage({ message }: Props) {
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