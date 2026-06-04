# Posibles Mejoras al Backend Expensy

> Análisis basado en estándares actuales de LangChain y LangGraph.
> **Nota de diseño**: El sistema es intencionalmente **stateless**. Cada request de chat es independiente; no hay memoria de conversación entre requests.

---

## 1. Arquitectura Actual (Resumen)

- **FastAPI** stateless con 2 endpoints de chat streaming (`personal` / `demo`) vía HTTP REST + SSE.
- **Supervisor** (`langgraph-supervisor`) que orquesta 2 agentes ReAct (`writer` y `reader`) creados con `create_agent`.
- **Tools REST directas**: Los agentes usan herramientas LangChain tipadas (`@tool`) que llaman a la REST API de Airtable via HTTP plano (`urllib`), sin SDK ni MCP.
- **Sin persistencia**: cada request recrea el grafo y no hay estado entre llamadas (diseño intencional).

---

## 2. Gaps Identificados

| # | Problema | Impacto |
|---|----------|---------|
| 1 | **No hay state schema** (`TypedDict` / `StateSchema`). El grafo opera sobre un dict plano. | Sin tipado, sin reducers, riesgo de pérdida de mensajes en updates internos del grafo. |
| 2 | **Recrea el grafo en cada request** (`create_expensy_graph(mode)` dentro de `stream_supervisor_response`). | Ineficiente; el grafo debería compilarse una vez y reutilizarse por modo. |
| 3 | Streaming filtra manualmente `on_chat_model_stream` de `astream_events`. | Debería usar `stream_mode="messages"` de LangGraph para un flujo más limpio y con metadatos. |
| 4 | **Sin `ToolNode` ni manejo de errores de tools**. | Si una tool falla, no se devuelve `ToolMessage` al LLM para recuperación. |
| 5 | **Sin `RetryPolicy` ni `recursion_limit`**. | Sin protección contra loops infinitos ni reintentos en fallos transitorios. |
| 6 | Prompts embebidos con f-strings en la creación del grafo. | Mejor pasar contexto vía `config` o state para mayor flexibilidad y evitar reconstrucción. |

---

## 3. Decisiones de Diseño Descartadas (Intencionalmente)

Las siguientes mejoras fueron evaluadas y **descartadas** porque no alinean con los requerimientos del producto:

| Mejora | Razón de Descarte |
|--------|-------------------|
| `MemorySaver` + `thread_id` | Cada consulta es puntual e independiente; no se requiere memoria de conversación. |
| `checkpointer` (PostgreSQL/SQLite) | Agregaría complejidad de infraestructura sin beneficio para el caso de uso actual. |
| Reducer de mensajes para historial entre requests | No aplica al modelo stateless; el historial se mantiene solo dentro del ciclo de vida de un único request. |
| `HumanInTheLoopMiddleware` / `interrupt` | Las acciones actuales (registrar/consultar gastos) no son destructivas ni irreversibles. |

---

## 4. Decisiones de Diseño Mantenidas (Conscientemente)

Las siguientes decisiones arquitectónicas se mantienen tras evaluación; no son gaps:

| Decisión | Justificación |
|----------|---------------|
| **Mantener `langgraph-supervisor`** | Aunque es un paquete de terceros, para un flujo con 2 agentes especializados (`writer`/`reader`) y enrutamiento binario, la abstracción es adecuada y reduce boilerplate. Se prefiere sobre construir un `StateGraph` manual con `Command` o un único `create_react_agent`, ya que preserva la separación de prompts especializados y la especialización de responsabilidades. |

---

## 5. Recomendaciones de Alto Nivel (Aplicables)

1. **Definir un `State` tipado** (`TypedDict`) para controlar el flujo interno del grafo durante un request, aunque no persista entre requests.
2. **Compilar el grafo una vez** por modo y cachearlo (evitar reconstrucción en cada request).
3. **Agregar `RetryPolicy`** en nodos que interactúan con Airtable y `recursion_limit` en la invocación del grafo.
4. **Migrar streaming** a `stream_mode="messages"` para un consumo más idiomático de LangGraph.
5. **Externalizar prompts** del f-string; pasar contexto (como `mode_label`) vía `configurable` en el `config` de invocación.

---

## 6. Notas de Implementación (Pendientes de Discusión)

- **Field IDs hardcodeados**: `field_ids.py` contiene los field IDs de Airtable. Regenerar con `python scripts/generate_field_ids.py` si cambian los campos en Airtable.
- **Cacheo del grafo**: ¿Global en memoria (variable de módulo) o usando `lru_cache`?
- **Estructura del `State`**: ¿Qué campos son necesarios para el flujo interno? (ej: `messages`, `mode`, `route`).
- **Nodo Supervisor**: ¿Se mantiene como LLM que decide, o se usa una clasificación más simple (ej: regex/keywords) para enrutar?
- **Manejo de errores de Airtable**: ¿Se quiere un fallback a mensaje de error genérico o que el agente intente recuperarse?
