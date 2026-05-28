from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from mcp_client import get_airtable_tools
from prompts import READER_AGENT_PROMPT, SUPERVISOR_PROMPT, WRITER_AGENT_PROMPT
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


async def create_expensy_graph(mode: Mode):
    model = create_model()
    tools = await get_airtable_tools(mode)
    
    base_id = settings.airtable_base_id_for_mode(mode)
    table_id = settings.airtable_expenses_table_id

    writer_agent = create_react_agent(
        model=model,
        tools=tools,
        name="expense_writer_agent",
        prompt=WRITER_AGENT_PROMPT.format(base_id=base_id, table_id=table_id),
    )

    reader_agent = create_react_agent(
        model=model,
        tools=tools,
        name="expense_reader_agent",
        prompt=READER_AGENT_PROMPT.format(base_id=base_id, table_id=table_id),
    )

    supervisor = create_supervisor(
        agents=[writer_agent, reader_agent],
        model=model,
        prompt=SUPERVISOR_PROMPT,
        add_handoff_back_messages=True,
        output_mode="full_history",
        reasoning_effort="low"
    )
    return supervisor.compile()


async def stream_supervisor_response(message: str, mode: Mode) -> AsyncIterator[str]:
    graph = await create_expensy_graph(mode)
    input_state = {"messages": [HumanMessage(content=message)]}

    async for event in graph.astream_events(
        input_state, config={"configurable": {"mode": mode}}, version="v2"
    ):
        if event.get("event") != "on_chat_model_stream":
            continue

        chunk = event.get("data", {}).get("chunk")
        content = getattr(chunk, "content", None)
        if isinstance(content, str) and content:
            yield content
