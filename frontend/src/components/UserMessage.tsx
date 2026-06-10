import { useRef, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessagePrimitive } from "@assistant-ui/react";

export function UserMessage() {
  const [copied, setCopied] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleCopy = useCallback(async () => {
    const text = contentRef.current?.textContent ?? "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Ignorar errores silenciosamente
    }
  }, []);

  return (
    <>
      <MessagePrimitive.Root className="messageBubble user">
        <div className="messageHeader">
          <span className="messageRole">Tu</span>
        </div>
        <MessagePrimitive.Parts>
          {({ part }) => {
            if (part.type === "text") {
              const text = (part as { text?: string }).text ?? "";
              return (
                <div ref={contentRef}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {text}
                  </ReactMarkdown>
                </div>
              );
            }
            return null;
          }}
        </MessagePrimitive.Parts>
      </MessagePrimitive.Root>
      <div className="userMessageFooter">
        <button
          type="button"
          className={`copyButton${copied ? " copied" : ""}`}
          onClick={handleCopy}
          aria-label={copied ? "Copiado" : "Copiar mensaje"}
        >
          {copied ? (
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
          )}
          <span>{copied ? "Copiado" : "Copiar"}</span>
        </button>
      </div>
    </>
  );
}
