# Expensy

Expensy es una aplicacion de chat para registrar y consultar gastos con lenguaje natural. El foco del proyecto no es solo la UI: esta construido como una pequena arquitectura agentic con LangChain, LangGraph, supervisor multiagente, tools tipadas y acceso a datos reales a traves de MCP.

La idea es que un usuario pueda escribir cosas como `registra cafe 3 USD en comida` o `cuanto gaste esta semana`, y que el sistema interprete la intencion, elija la herramienta correcta y responda en streaming.

## Lo Interesante del Proyecto

- Orquestacion multiagente con `langgraph-supervisor` 🤖: hay un supervisor que enruta cada mensaje a un agente especialista de escritura o lectura de gastos.
- Tools reales con LangChain: el modelo no responde solo con texto; puede ejecutar herramientas estructuradas para registrar y recuperar gastos.
- Integracion MCP con Airtable 🔌: en vez de hablar directo con la API, el backend consume el servidor MCP oficial de Airtable y resuelve base, tabla y schema de forma dinamica.
- Backend stateless: no hay base de datos local ni memoria de conversacion; cada request es autocontenido, lo que simplifica despliegue y seguridad.
- Streaming end-to-end ⚡: FastAPI responde con stream compatible con AI SDK UI y el frontend consume el resultado con `useChat`.
- Separacion de entornos: existen rutas y credenciales distintas para modo `personal` y modo `demo`, evitando cruces de datos.
- Diseño de prompts con restricciones operativas: el supervisor y los agentes tienen instrucciones para no inventar gastos, tasas ni resultados de Airtable.

## Stack

- Frontend: React, Vite, `@ai-sdk/react`, `ai`
- Backend: FastAPI, LangChain 1.x, LangGraph 1.x, `langgraph-supervisor`
- Data access: Airtable MCP oficial en `https://mcp.airtable.com/mcp`
- Modelo LLM: configurable por entorno con `OPENAI_MODEL`

## Arquitectura IA

Flujo de alto nivel:

1. El frontend envia solo `{ "message": "..." }` al backend.
2. FastAPI valida el bearer token y selecciona el modo `personal` o `demo`.
3. El supervisor LangGraph recibe el texto y decide si debe delegar en:
   `expense_writer_agent` para registrar gastos.
4. O en:
   `expense_reader_agent` para consultar o resumir gastos.
5. El agente especialista invoca una tool LangChain.
6. La tool usa `langchain_mcp_adapters` para conectarse al MCP oficial de Airtable.
7. El resultado vuelve al usuario en streaming.

Capacidades que demuestra esta arquitectura:

- Routing agentico por intencion
- Tool calling con schemas tipados
- Integracion MCP en Python
- Separacion entre orquestacion, tools y acceso a datos
- Streaming de tokens hacia una UI real
- Aislamiento de entornos y credenciales

## Features IA Implementadas

- `register_expense`
  Interpreta datos de gasto y crea registros en Airtable.

- `retrieve_expenses`
  Recupera gastos por consulta textual, filtros o necesidad de resumen.

- `get_bolivar_rate`
  Tool placeholder para una futura integracion de tasa de cambio.

- Supervisor con especializacion
  El sistema no usa un solo agente generalista. Usa un supervisor y dos agentes con responsabilidades diferentes para reducir ambiguedad y mejorar control.

- Guardrails de comportamiento
  Los prompts fuerzan respuestas en espanol, prohiben inventar resultados y delimitan claramente el dataset activo.

## Estructura del Repo

- `frontend/`
  Cliente React con `useChat` y `DefaultChatTransport`.

- `backend/main.py`
  Endpoints, auth y streaming SSE compatible con AI SDK UI.

- `backend/supervisor.py`
  Grafo supervisor y agentes especialistas.

- `backend/agents.py`
  Tools LangChain para registrar, consultar y obtener tasa placeholder.

- `backend/mcp_client.py`
  Wrapper MCP para Airtable con resolucion dinamica de base, tabla y schema.

- `current-job.md`
  Plan de implementacion documentado.

## Variables Backend

Crear `backend/.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

PERSONAL_API_TOKEN=personal-token
DEMO_API_TOKEN=demo-token

AIRTABLE_MCP_URL=https://mcp.airtable.com/mcp
AIRTABLE_PERSONAL_PAT=pat...
AIRTABLE_DEMO_PAT=pat...
AIRTABLE_PERSONAL_BASE_NAME=Expensy Personal
AIRTABLE_DEMO_BASE_NAME=Expensy Demo
AIRTABLE_EXPENSES_TABLE_NAME=Expenses

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## Comandos

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

## Endpoints

- `POST /api/chat/personal/stream`
- `POST /api/chat/demo/stream`
- `GET /health`

Ejemplo:

```bash
curl -N -X POST http://localhost:8000/api/chat/demo/stream \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"registra cafe 3 USD en comida\"}"
```

El stream usa el protocolo de AI SDK UI con `x-vercel-ai-ui-message-stream: v1`.

## Que Senala Bien en una Postulacion IA

- Uso real de LangChain y LangGraph, no solo wrappers de chat.
- Supervisor multiagente con tools especializadas.
- MCP como capa de integracion con sistemas externos.
- Streaming full-stack desde el modelo hasta la interfaz.
- Backend disenado para entornos separados, seguridad por token y cero dependencia en memoria conversacional local.

## Limitaciones Actuales

- `get_bolivar_rate` es placeholder.
- La calidad de la consulta depende de la estructura real de la tabla de Airtable.
- No hay memoria multi-turn ni historial persistente por diseño.
