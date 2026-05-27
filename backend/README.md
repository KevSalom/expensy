# Expensy Backend

FastAPI stateless para Expensy. Recibe mensajes de chat, valida bearer tokens y delega en un supervisor LangGraph/LangChain que usa Airtable MCP.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## `.env`

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

## Endpoints

| Metodo | Ruta | Uso |
| --- | --- | --- |
| GET | `/health` | Healthcheck |
| POST | `/api/chat/personal/stream` | Chat contra Airtable personal |
| POST | `/api/chat/demo/stream` | Chat contra Airtable demo |

Los endpoints de chat reciben:

```json
{ "message": "registra cafe 3 USD en comida" }
```

Autenticacion:

```http
Authorization: Bearer <PERSONAL_API_TOKEN o DEMO_API_TOKEN>
```

No hay base de datos local, historial ni checkpointer de LangGraph.
