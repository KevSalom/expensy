# Expensy

Expensy es una aplicacion de chat para registrar y consultar gastos con lenguaje natural. El foco del proyecto no es solo la UI: esta construido como una pequena arquitectura agentic con LangChain, LangGraph, supervisor multiagente, tools tipadas y acceso a datos reales a traves de la REST API de Airtable.

La idea es que un usuario pueda escribir cosas como `registra cafe 3 USD en comida` o `cuanto gaste esta semana`, y que el sistema interprete la intencion, elija la herramienta correcta y responda en streaming.

## Lo Interesante del Proyecto

- Orquestacion multiagente con `langgraph-supervisor`: hay un supervisor que enruta cada mensaje a un agente especialista de escritura o lectura de gastos.
- Tools reales con LangChain: el modelo no responde solo con texto; puede ejecutar herramientas estructuradas para registrar y recuperar gastos.
- Integracion REST directa con Airtable: el backend se conecta a `https://api.airtable.com/v0/` con HTTP plano (sin SDK ni MCP), usando `urllib` y un cliente liviano que resuelve base, tabla y schema de forma dinamica.
- Field IDs precargados: los IDs de campo se generan con un script y se cachean en `field_ids.py`, evitando llamadas extras al schema.
- Backend stateless: no hay base de datos local ni memoria de conversacion; cada request es autocontenido, lo que simplifica despliegue y seguridad.
- Streaming end-to-end: FastAPI responde con stream compatible con AI SDK UI y el frontend consume el resultado con `useChat`.
- Separacion de entornos: existen rutas y credenciales distintas para modo `personal` y modo `demo`, evitando cruces de datos.
- Diseno de prompts con restricciones operativas: el supervisor y los agentes tienen instrucciones para no inventar gastos, tasas ni resultados de Airtable.

## Stack

- Frontend: React, Vite, `@ai-sdk/react`, `ai`, `assistant-ui`
- Backend: FastAPI, LangChain 1.x, LangGraph 1.x, `langgraph-supervisor`
- Data access: Airtable REST API (`https://api.airtable.com/v0/`)
- Modelo LLM: configurable por entorno con `OPENAI_MODEL`

## Arquitectura IA

Flujo de alto nivel:

1. El frontend envia solo `{ "message": "..." }` al backend.
2. FastAPI valida el bearer token y selecciona el modo `personal` o `demo`.
3. El supervisor LangGraph recibe el texto y decide si debe delegar en:
   `expense_writer_agent` para registrar gastos.
4. O en:
   `expense_reader_agent` para consultar o resumir gastos.
5. El agente especialista invoca una tool LangChain tipada (`rest_tools.py`).
6. La tool llama al cliente `AirtableREST` (`airtable_rest.py`) que hace HTTP requests directos a la REST API de Airtable.
7. El resultado vuelve al usuario en streaming.

Capacidades que demuestra esta arquitectura:

- Routing agentico por intencion
- Tool calling con schemas tipados
- Cliente REST custom sin dependencias externas
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

- `backend/rest_tools.py`
  Tools LangChain tipadas para registrar, consultar y buscar gastos via REST API.

- `backend/airtable_rest.py`
  Cliente HTTP liviano para la REST API de Airtable (sin SDK, sin MCP).

- `backend/field_ids.py`
  Mapeo cacheado de nombres de campo a Field IDs de Airtable.

- `backend/prompts.py`
  Prompts del supervisor y agentes con reglas operativas.

- `backend/config.py`
  Configuracion con Pydantic Settings desde `.env`.

- `backend/scripts/`
  Scripts utilitarios: generacion de field IDs, tests, debug.

- `current-job.md`
  Plan de implementacion documentado.

## Variables Backend

Crear `backend/.env` (ver `backend/.env.example`):

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Auth (name + password, JWT).
JWT_SECRET=replace-with-32-byte-hex
USERS_JSON=[{"name":"kev","password_hash":"$2b$12$..."}]
DEMO_PASSWORD_HASH=$2b$12$...

AIRTABLE_PERSONAL_PAT=pat...
AIRTABLE_DEMO_PAT=pat...
AIRTABLE_PERSONAL_BASE_ID=app...
AIRTABLE_DEMO_BASE_ID=app...
AIRTABLE_EXPENSES_TABLE_ID=tbl...

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Generar secretos

```bash
# JWT_SECRET (32 bytes hex)
openssl rand -hex 32

# Hash bcrypt para un usuario o para el modo demo
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('tu_clave'))"
```

## Autenticacion

El flujo de login es `POST /api/auth/login` con `{ name?, password, mode }`:

- `mode: "personal"` requiere `name` + `password`; valida contra `USERS_JSON` (hash bcrypt).
- `mode: "demo"` requiere solo `password`; valida contra `DEMO_PASSWORD_HASH`.

El backend responde con `{ token, name, mode, expires_at }`. El JWT se firma con HS256 usando `JWT_SECRET` y expira a 7 dias en personal o 1 hora en demo.

El frontend guarda el token en `localStorage` (personal) o `sessionStorage` (demo) y lo envia en cada request como `Authorization: Bearer <token>`. El modo demo **no persiste entre cierres de pestaña**.

Endpoints:

- `POST /api/auth/login` body `{name?, password, mode}` → `{token, name, mode, expires_at}`
- `POST /api/auth/logout` → `{ok: true}` (no-op; el cliente limpia el storage)
- `GET /api/auth/me` → `{name, mode, expires_at}` o 401

Los endpoints de chat (`/api/chat/personal/stream`, `/api/chat/demo/stream`) requieren JWT del modo correspondiente. Un token personal no funciona en el endpoint demo y viceversa.

Ejemplo curl:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name":"kev","password":"tu_clave","mode":"personal"}'

# Uso con el token
TOKEN="..."
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me

curl -N -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/chat/personal/stream \
  -d '{"message":"hola"}'
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

## Limitaciones Actuales

- `get_bolivar_rate` es placeholder.
- La calidad de la consulta depende de la estructura real de la tabla de Airtable.
- No hay memoria multi-turn ni historial persistente por diseño.
- Los Field IDs se regeneran manualmente con `scripts/generate_field_ids.py` si cambia el schema.
