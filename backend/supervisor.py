from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from agents import create_expensy_tools
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


def create_expensy_graph(mode: Mode):
    model = create_model()
    register_expense, retrieve_expenses, get_bolivar_rate = create_expensy_tools(mode)
    mode_label = "personal" if mode == "personal" else "demo"

    writer_agent = create_react_agent(
        model=model,
        tools=[register_expense, get_bolivar_rate],
        name="expense_writer_agent",
        prompt=(
            "Eres el agente escritor de Expensy. Tu unica responsabilidad es "
            "registrar gastos. Antes de llamar register_expense debes tener monto, "
            "moneda y categoria. Si falta alguno, pide una aclaracion breve. "
            "No inventes datos y opera solo en el entorno "
            f"{mode_label}."
        ),
    )

    reader_agent = create_react_agent(
        model=model,
        tools=[retrieve_expenses, get_bolivar_rate],
        name="expense_reader_agent",
        prompt=(
            "Eres el agente lector de Expensy. Tu unica responsabilidad es "
            "consultar, buscar y resumir gastos. Usa retrieve_expenses para "
            "obtener datos de Airtable. No inventes resultados y opera solo en "
            f"el entorno {mode_label}."
        ),
    )

    supervisor = create_supervisor(
        agents=[writer_agent, reader_agent],
        model=model,
        prompt=(
            "Eres el supervisor principal de Expensy, una app de gastos. "
            "Responde siempre en espanol claro y breve. Interpreta el texto "
            "natural del usuario y delega en expense_writer_agent cuando quiera "
            "registrar un gasto, o en expense_reader_agent cuando quiera consultar "
            "gastos. No inventes gastos, tasas, bases, tablas ni resultados de "
            "Airtable. Si Airtable no confirma una accion, dilo explicitamente. "
            "No uses memoria de conversaciones previas. "
            f"Este request pertenece al modo {mode_label}; no cruces datos entre "
            "personal y demo."
        ),
    )
    return supervisor.compile()


async def stream_supervisor_response(message: str, mode: Mode) -> AsyncIterator[str]:
    graph = create_expensy_graph(mode)
    input_state = {"messages": [HumanMessage(content=message)]}

    async for event in graph.astream_events(input_state, version="v2"):
        if event.get("event") != "on_chat_model_stream":
            continue

        chunk = event.get("data", {}).get("chunk")
        content = getattr(chunk, "content", None)
        if isinstance(content, str) and content:
            yield content
