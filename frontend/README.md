# Expensy Frontend

React + Vite UI para conversar con el backend de Expensy.

## Setup

```bash
pnpm install
pnpm dev
```

Variable opcional:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Integracion de chat

La UI usa `useChat` de `@ai-sdk/react` con `DefaultChatTransport` de `ai`.

- Modo `Demo`: llama `/api/chat/demo/stream`.
- Modo `Personal`: llama `/api/chat/personal/stream`.
- Header: `Authorization: Bearer <token>`.
- Body enviado al backend: `{ "message": "..." }`.

El token se mantiene solo en memoria del navegador y no se guarda en localStorage.
