"""
Script para estudiar que devuelve el grafo de LangGraph/LangChain.
Ejecuta: python scripts/debug_stream.py "cuanto gasté en comida este mes"
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supervisor import create_expensy_graph, Mode
from langchain_core.messages import HumanMessage


async def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/debug_stream.py <mensaje>")
        sys.exit(1)

    message = sys.argv[1]
    mode: Mode = "personal"
    log_file = Path(__file__).parent / "stream_log.jsonl"

    print(f"Mensaje: {message}")
    print(f"Log file: {log_file}")
    print("=" * 60)

    graph = await create_expensy_graph(mode)
    input_state = {"messages": [HumanMessage(content=message)]}

    all_events = []

    async for event in graph.astream(
        input_state,
        config={"configurable": {"mode": mode}, "recursion_limit": 50},
        stream_mode="messages"
    ):
        msg, metadata = event

        try:
            msg_kwargs = {k: v for k, v in vars(msg).items() if k != "content"} if hasattr(msg, "__dict__") else {}
        except Exception:
            msg_kwargs = {"error": "could not extract vars"}
        event_data = {
            "msg_type": type(msg).__name__,
            "msg_content": getattr(msg, "content", None),
            "msg_kwargs": msg_kwargs,
            "metadata": {k: str(v) for k, v in metadata.items()},
        }
        all_events.append(event_data)

        # Console output
        langgraph_node = metadata.get("langgraph_node", "unknown")
        msg_type = type(msg).__name__
        content = getattr(msg, "content", None)

        print(f"\n[node={langgraph_node}] {msg_type}")
        if isinstance(content, str):
            preview = content[:150] + "..." if len(content) > 150 else content
            print(f"  content: {preview}")
        elif content is None:
            print(f"  content: None")
        else:
            print(f"  content: {type(content).__name__} = {str(content)[:150]}")

    # Save full log
    with open(log_file, "w", encoding="utf-8") as f:
        for event in all_events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"\n{'=' * 60}")
    print(f"Total eventos: {len(all_events)}")
    print(f"Log guardado: {log_file}")

    # Summary by node
    nodes = {}
    for e in all_events:
        node = e["metadata"].get("langgraph_node", "unknown")
        nodes[node] = nodes.get(node, 0) + 1
    print(f"Eventos por node: {nodes}")


if __name__ == "__main__":
    asyncio.run(main())