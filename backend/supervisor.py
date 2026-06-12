from __future__ import annotations

import time
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone, timedelta
from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor

from prompts import make_reader_prompt, make_writer_prompt, SUPERVISOR_PROMPT
from field_ids import get_field_ids
from rest_tools import get_rest_tools
from config import settings

Mode = Literal["personal", "demo"]


class StreamEvent(TypedDict):
    type: Literal["progress", "final"]
    text: str


def create_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.1,
        streaming=True,
        max_tokens=4096,
    )


def format_field_map(field_map: dict[str, str]) -> str:
    if not field_map:
        return "(No se pudo obtener el mapeo de campos)"
    lines = [f"  - `{name}` -> `{id}`" for name, id in sorted(field_map.items())]
    return "\n".join(lines)


async def create_expensy_graph(mode: Mode):
    start = time.time()
    print(f"[PERF] Iniciando create_expensy_graph...")
    
    model = create_model()
    print(f"[PERF]   Model creado: {time.time()-start:.3f}s")
    
    tools = get_rest_tools(mode)
    print(f"[PERF]   REST tools cargadas: {time.time()-start:.3f}s")
    
    base_id = settings.airtable_base_id_for_mode(mode)
    table_id = settings.airtable_expenses_table_id
    
    field_map = get_field_ids(mode)
    field_map_str = format_field_map(field_map)
    caracas_tz = timezone(timedelta(hours=-4))
    today = datetime.now(caracas_tz).date().isoformat()

    writer_agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=make_writer_prompt(
            base_id=base_id, table_id=table_id, field_map_str=field_map_str, today=today
        ),
        name="expense_writer_agent",
    )

    reader_agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=make_reader_prompt(
            base_id=base_id, table_id=table_id, field_map_str=field_map_str, today=today
        ),
        name="expense_reader_agent",
    )

    supervisor = create_supervisor(
        agents=[writer_agent, reader_agent],
        model=model,
        prompt=SUPERVISOR_PROMPT,
    )
    compiled = supervisor.compile()
    print(f"[PERF] Grafo completo: {time.time()-start:.3f}s")
    return compiled


def _agent_to_friendly_message(agent_name: str, content: str) -> str | None:
    """Convert raw agent message to friendly UI message."""
    if not content or not isinstance(content, str):
        return None
    
    content_lower = content.lower()
    
    if "transfer" in content_lower or "delegat" in content_lower:
        return None
    
    if agent_name == "expense_reader_agent":
        if "buscar" in content_lower or "consultar" in content_lower or "gastos" in content_lower:
            return "Buscando tus gastos"
        if "encontr" in content_lower or "registros" in content_lower or "encontre" in content_lower:
            return "Analizando registros"
        if "sumar" in content_lower or "total" in content_lower or "gast" in content_lower:
            return "Calculando totales"
        if "ultimo" in content_lower or "último" in content_lower:
            return "Preparando respuesta"
        return "Consultando gastos"
    
    if agent_name == "expense_writer_agent":
        if "registrar" in content_lower or "guardar" in content_lower or "crear" in content_lower:
            return "Guardando registro"
        if "registrad" in content_lower or "guardado" in content_lower or "creado" in content_lower:
            return "Registro guardado"
        if "confirm" in content_lower or "listo" in content_lower:
            return "Confirmando"
        return "Procesando registro"
    
    return None


async def stream_supervisor_response(message: str, mode: Mode) -> AsyncIterator[str]:
    async for event in stream_supervisor_events(message, mode):
        if event["type"] == "final":
            yield event["text"]


async def stream_supervisor_events(message: str, mode: Mode) -> AsyncIterator[StreamEvent]:
    start = time.time()
    print(f"[PERF] stream_supervisor_events iniciado")
    
    graph = await create_expensy_graph(mode)
    print(f"[PERF]   Grafo listo: {time.time()-start:.3f}s")
    
    input_state = {"messages": [HumanMessage(content=message)]}
    
    event_count = 0
    final_started = False
    
    async for event in graph.astream(
        input_state,
        config={"configurable": {"mode": mode}, "recursion_limit": 50},
        stream_mode="messages",
    ):
        event_count += 1
        msg, metadata = event
        langgraph_node = metadata.get("langgraph_node", "unknown")
        
        print(f"[PERF]   msg #{event_count} from node={langgraph_node}, type={type(msg).__name__}")
        
        if langgraph_node == "supervisor":
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content:
                if content.lower().startswith("thought"):
                    content = content[7:].lstrip("\n ")
                print(f"[PERF]     final content: '{content[:80]}...' " if len(content) > 80 else f"[PERF]     final content: '{content}'")
                if not final_started:
                    final_started = True
                yield {"type": "final", "text": content}
        else:
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content:
                friendly = _agent_to_friendly_message(langgraph_node, content)
                if friendly:
                    print(f"[PERF]     progress: {friendly}")
                    yield {"type": "progress", "text": friendly}
    
    print(f"[PERF] Stream completo: {time.time()-start:.3f}s ({event_count} eventos)")