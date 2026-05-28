import { useMemo, useState } from 'react'
import { useChat, type UIMessage } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

type ChatMode = 'personal' | 'demo'
type TextPart = { type: string; text?: string }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const chatRuntime: { mode: ChatMode; token: string } = {
  mode: 'demo',
  token: '',
}

function getMessageText(message: UIMessage): string {
  return (message.parts ?? [])
    .map((part) => {
      const textPart = part as TextPart
      return textPart.type === 'text' ? textPart.text ?? '' : ''
    })
    .join('')
}

function modeEndpoint(mode: ChatMode): string {
  return `${API_BASE_URL}/api/chat/${mode}/stream`
}

function App() {
  const [mode, setMode] = useState<ChatMode>('demo')
  const [token, setToken] = useState('')
  const [input, setInput] = useState('')

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: modeEndpoint('demo'),
        prepareSendMessagesRequest: ({ messages }) => {
          const lastMessage = messages[messages.length - 1]
          return {
            api: modeEndpoint(chatRuntime.mode),
            headers: {
              Authorization: `Bearer ${chatRuntime.token.trim()}`,
            },
            body: {
              message: lastMessage ? getMessageText(lastMessage) : '',
            },
          }
        },
      }),
    [],
  )

  const { messages, sendMessage, stop, status, error, setMessages, clearError } =
    useChat({
      transport,
    })

  const isStreaming = status === 'submitted' || status === 'streaming'
  const canSend = input.trim().length > 0 && token.trim().length > 0 && !isStreaming

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = input.trim()
    if (!text || !canSend) return
    setInput('')
    await sendMessage({ text })
  }

  function handleModeChange(nextMode: ChatMode) {
    chatRuntime.mode = nextMode
    setMode(nextMode)
    clearError()
  }

  function handleTokenChange(nextToken: string) {
    chatRuntime.token = nextToken
    setToken(nextToken)
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
              className={mode === 'demo' ? 'active' : ''}
              onClick={() => handleModeChange('demo')}
            >
              Demo
            </button>
            <button
              type="button"
              className={mode === 'personal' ? 'active' : ''}
              onClick={() => handleModeChange('personal')}
            >
              Personal
            </button>
          </div>

          <label className="tokenField">
            <span>Contraseña {mode === 'demo' ? 'demo' : 'personal'}</span>
            <input
              type="password"
              value={token}
              placeholder={mode === 'demo' ? 'Contraseña demo' : 'Contraseña personal'}
              onChange={(event) => handleTokenChange(event.target.value)}
            />
            <small>Usa la contraseña configurada para este modo.</small>
          </label>

          <button
            type="button"
            className="secondaryAction"
            onClick={() => {
              stop()
              setMessages([])
              clearError()
            }}
          >
            Limpiar chat
          </button>
        </aside>

        <section className="chatPanel" aria-label="Chat de Expensy">
          <div className="messageList">
            {messages.length === 0 ? (
              <div className="emptyState">
                <p>Prueba con “registra cafe 3 USD en comida” o “cuanto gaste esta semana”.</p>
              </div>
            ) : (
              messages.map((message) => (
                <article
                  key={message.id}
                  className={`messageBubble ${message.role === 'user' ? 'user' : 'assistant'}`}
                >
                  <span className="messageRole">
                    {message.role === 'user' ? 'Tu' : 'Expensy'}
                  </span>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {getMessageText(message)}
                  </ReactMarkdown>
                </article>
              ))
            )}
          </div>

          {error ? (
            <div className="errorBox" role="alert">
              <span>{error.message}</span>
              <button type="button" onClick={clearError}>
                Cerrar
              </button>
            </div>
          ) : null}

          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              value={input}
              rows={2}
              placeholder="Escribe un gasto o una consulta..."
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  event.currentTarget.form?.requestSubmit()
                }
              }}
            />
            <div className="composerActions">
              <button type="button" onClick={stop} disabled={!isStreaming}>
                Detener
              </button>
              <button type="submit" disabled={!canSend}>
                Enviar
              </button>
            </div>
          </form>
        </section>
      </section>
    </main>
  )
}

export default App
