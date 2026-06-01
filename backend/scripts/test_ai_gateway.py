#!/usr/bin/env python3
"""Script simple para probar AI Gateway con LangGraph."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from config import settings


async def main():
    print("Configuración:")
    print(f"  Model: {settings.openai_model}")
    print(f"  Base URL: {settings.openai_base_url}")
    print()
    
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.7,
    )
    
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt="Eres un asistente útil y conciso.",
    )
    
    question = "¿Cuál es la capital de Francia?"
    print(f"Pregunta: {question}")
    print()
    
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=question)]
    })
    
    print("Respuesta:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
