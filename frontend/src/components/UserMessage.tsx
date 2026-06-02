import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessagePrimitive } from "@assistant-ui/react";


export function UserMessage() {

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