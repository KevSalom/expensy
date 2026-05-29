from __future__ import annotations

import time
from collections.abc import AsyncIterator
from datetime import date
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from prompts import make_reader_prompt, make_writer_prompt, SUPERVISOR_PROMPT
from airtable_rest import get_writable_field_ids
from rest_tools import get_rest_tools
from config import settings

Mode = Literal["personal", "demo"]


def create_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
        streaming=True,
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
    
    t0 = time.time()
    field_map = get_writable_field_ids(mode)
    print(f"[PERF]   get_writable_field_ids: {time.time()-t0:.3f}s")
    
    field_map_str = format_field_map(field_map)
    today = date.today().isoformat()

    writer_agent = create_react_agent(
        model=model,
        tools=tools,
        name="expense_writer_agent",
        prompt=make_writer_prompt(
            base_id=base_id, table_id=table_id, field_map_str=field_map_str, today=today
        ),
    )

    reader_agent = create_react_agent(
        model=model,
        tools=tools,
        name="expense_reader_agent",
        prompt=make_reader_prompt(
            base_id=base_id, table_id=table_id, field_map_str=field_map_str, today=today
        ),
    )

    supervisor = create_supervisor(
        agents=[writer_agent, reader_agent],
        model=model,
        prompt=SUPERVISOR_PROMPT,
    )
    compiled = supervisor.compile()
    print(f"[PERF] Grafo completo: {time.time()-start:.3f}s")
    return compiled


async def stream_supervisor_response(message: str, mode: Mode) -> AsyncIterator[str]:
    start = time.time()
    print(f"[PERF] stream_supervisor_response iniciado")
    
    graph = await create_expensy_graph(mode)
    print(f"[PERF]   Grafo listo: {time.time()-start:.3f}s")
    
    input_state = {"messages": [HumanMessage(content=message)]}
    
    event_count = 0
    
    async for event in graph.astream(
        input_state,
        config={"configurable": {"mode": mode}, "recursion_limit": 50},
        stream_mode="messages"
    ):
        event_count += 1
        msg, metadata = event
        langgraph_node = metadata.get("langgraph_node", "unknown")
        
        print(f"[PERF]   msg #{event_count} from node={langgraph_node}, type={type(msg).__name__}")
        
        if langgraph_node != "supervisor":
            print(f"[PERF]     >>> SKIPPING (not supervisor)")
            continue
        
        content = getattr(msg, "content", None)
        if isinstance(content, str) and content:
            print(f"[PERF]     content: '{content[:80]}...' " if len(content) > 80 else f"[PERF]     content: '{content}'")
            yield content
    
    print(f"[PERF] Stream completo: {time.time()-start:.3f}s ({event_count} eventos)")