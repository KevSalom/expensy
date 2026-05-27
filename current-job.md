# current-job.md - Plan de Implementacion de Expensy

## Resumen

Expensy es una app de chat para registrar y consultar gastos usando React + Vite en frontend y FastAPI + LangGraph/LangChain en backend. No hay base de datos local ni persistencia de conversacion: cada request se procesa de forma stateless. La fuente de datos es Airtable usando su servidor MCP oficial.

Decisiones implementadas:
- Request del chat: `POST` con JSON `{ "message": "texto del usuario" }`.
- Autenticacion de endpoints propios: `Authorization: Bearer <token>`.
- Airtable MCP: servidor HTTP oficial `https://mcp.airtable.com/mcp`.
- Auth Airtable MCP: PAT por entorno con header `Authorization: Bearer <AIRTABLE_PAT>`.
- Frontend: `useChat` con `DefaultChatTransport` y `prepareSendMessagesRequest` para enviar solo `{ message }`.

## Tareas de Implementacion

1. Limpiar backend actual
- Eliminar dependencia funcional de SQLite, SQLModel, `ChatHistory`, sesiones y endpoints de historial.
- Quitar inicializacion de base de datos.
- Mantener FastAPI, CORS, logging basico y streaming.
- Dejar backend stateless: cada endpoint recibe texto, llama al supervisor y devuelve stream.

2. Configuracion
- Centralizar variables en `backend/config.py` con `BaseSettings`.
- Requerir `OPENAI_API_KEY`, `OPENAI_MODEL`, tokens propios, PATs Airtable, nombres de base y tabla.
- Usar `AIRTABLE_MCP_URL=https://mcp.airtable.com/mcp` por defecto.
- No hardcodear secretos, base IDs ni table IDs.

3. Endpoints protegidos
- Crear `POST /api/chat/personal/stream`.
- Crear `POST /api/chat/demo/stream`.
- Ambos reciben `{ "message": string }`.
- Ambos validan `Authorization: Bearer ...`.
- `personal` usa token/PAT/base personal.
- `demo` usa token/PAT/base demo.
- Responder `401` ante token ausente o invalido y `422` ante mensaje invalido.

4. Airtable MCP
- Crear `backend/mcp_client.py`.
- Usar `langchain_mcp_adapters.client.MultiServerMCPClient`.
- Configurar servidor `airtable` con transporte `streamable_http`, URL oficial y bearer PAT del modo.
- Resolver datos sin asumir IDs:
  - `search_bases` busca base por nombre.
  - `list_tables_for_base` busca tabla de gastos por nombre.
  - `get_table_schema` obtiene schema antes de operar.
- Registrar gastos con `create_records_for_table`.
- Consultar gastos con `search_records` si hay query o `list_records_for_table` como fallback.
- No crear mas de 10 records por request; la app actual crea un record por llamada.

5. Herramientas custom
- Crear `backend/agents.py`.
- Definir `register_expense` para registrar monto, moneda, categoria, fecha, descripcion y cuenta/fuente.
- Definir `retrieve_expenses` para consultar por texto, fecha, categoria, moneda o resumen.
- Definir `get_bolivar_rate` como placeholder con `rate: null`.
- Cada tool tiene schema Pydantic y descripcion explicita para reducir alucinaciones.

6. Supervisor LangGraph
- Crear `backend/supervisor.py`.
- Usar `langgraph-supervisor` con `create_supervisor`.
- Crear `expense_writer_agent` para registro.
- Crear `expense_reader_agent` para consultas.
- Compilar sin checkpointer ni store.
- Prompt del supervisor fuerza idioma espanol, separacion personal/demo y prohibicion de inventar resultados.

7. Streaming backend
- Implementar `stream_supervisor_response(message, mode)`.
- Convertir texto entrante en `HumanMessage`.
- Ejecutar el grafo con `astream_events`.
- Exponer stream compatible con AI SDK UI:
  - header `x-vercel-ai-ui-message-stream: v1`
  - eventos `start`, `text-start`, `text-delta`, `text-end`, `finish`
- Manejar errores con mensaje amable y logs sin secretos.

8. Frontend React/Vite
- Crear `frontend/src`.
- Usar `@ai-sdk/react` `useChat`.
- Agregar dependencia directa `ai`.
- Configurar `DefaultChatTransport` con endpoint segun modo, bearer token y `prepareSendMessagesRequest`.
- UI minima:
  - titulo `Expensy`
  - selector `Personal` / `Demo`
  - input de token
  - lista de mensajes
  - composer
  - botones enviar, detener y limpiar
  - estados loading/error
- No persistir token en localStorage.

9. Requirements y README
- Actualizar `backend/requirements.txt` con FastAPI, LangChain 1.x, LangGraph 1.x, MCP adapters y supervisor.
- Eliminar dependencias de SQLModel/SQLite.
- Documentar arquitectura, variables `.env`, comandos, endpoints y ejemplos curl.

## Test Plan

- Backend:
  - Sin token devuelve `401`.
  - Token demo no funciona en endpoint personal.
  - `{ "message": "" }` devuelve `422`.
  - “registre cafe 3 dolares” usa flujo de registro.
  - “cuanto gaste esta semana” usa flujo de consulta.
  - Si MCP falla, stream devuelve error amable.
- Airtable MCP:
  - `search_bases` encuentra base personal y demo por nombre.
  - `list_tables_for_base` encuentra tabla de gastos.
  - `create_records_for_table` crea un gasto valido.
  - `list_records_for_table` consulta gastos existentes.
  - No se crean mas de 10 records en una llamada.
- Frontend:
  - Build de Vite pasa.
  - Modo demo llama endpoint demo.
  - Modo personal llama endpoint personal.
  - Request body contiene solo `{ message }`.
  - UI muestra stream mientras llega.

## Supuestos

- Airtable MCP oficial esta disponible en `https://mcp.airtable.com/mcp`.
- Cada PAT tiene permisos solo sobre la base correspondiente.
- La tabla de gastos existe o sera creada manualmente antes de probar integracion real.
- No se implementa memoria de conversacion ni BBDD local.
