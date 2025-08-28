"""Example usage of LangChain-based memory manager."""

import asyncio
from uuid import uuid4

from novitas.agents.memory import LangChainMemoryManager
from novitas.core.models import MemoryType
from novitas.core.protocols import DatabaseManager


class MockDatabaseManager:
    """Mock database manager for demonstration."""

    def __init__(self):
        self.memory_store = {}

    async def save_agent_memory(self, agent_id, memory_data):
        """Save agent memory."""
        self.memory_store[str(agent_id)] = memory_data
        print(f"Saved memory for agent {agent_id}")

    async def load_agent_memory(self, agent_id):
        """Load agent memory."""
        return self.memory_store.get(str(agent_id))


class MockAgent:
    """Mock agent for demonstration."""

    def __init__(self, name: str):
        self.id = uuid4()
        self.name = name


async def main():
    """Demonstrate LangChain memory manager usage."""
    print("=== LangChain Memory Manager Example ===\n")

    # Create mock database manager
    db_manager = MockDatabaseManager()

    # Create LangChain memory manager
    memory_manager = LangChainMemoryManager(database_manager=db_manager)

    # Create a mock agent
    agent = MockAgent("Test Agent")
    print(f"Created agent: {agent.name} (ID: {agent.id})")

    # Register the agent
    await memory_manager.register_agent(agent)
    print("✓ Agent registered for memory management\n")

    # Add different types of memory
    print("Adding memory items...")

    # Conversation memory (will be added to LangChain)
    conv_id = await memory_manager.add_memory(
        agent_id=agent.id,
        memory_type=MemoryType.CONVERSATION,
        content={
            "input": "Hello, how are you?",
            "output": "I'm doing well, thank you!",
        },
        tags=["greeting"],
        importance=0.8,
    )
    print(f"✓ Added conversation memory (ID: {conv_id})")

    # Knowledge memory
    knowledge_id = await memory_manager.add_memory(
        agent_id=agent.id,
        memory_type=MemoryType.KNOWLEDGE,
        content={
            "fact": "Python is a programming language",
            "source": "general knowledge",
        },
        tags=["programming", "python"],
        importance=0.9,
    )
    print(f"✓ Added knowledge memory (ID: {knowledge_id})")

    # Experience memory with TTL
    experience_id = await memory_manager.add_memory(
        agent_id=agent.id,
        memory_type=MemoryType.EXPERIENCE,
        content={
            "experience": "Successfully completed a task",
            "duration": "5 minutes",
        },
        tags=["success", "task"],
        importance=0.7,
        ttl=3600.0,  # 1 hour
    )
    print(f"✓ Added experience memory with TTL (ID: {experience_id})")

    print()

    # Get all memory
    all_memory = await memory_manager.get_memory(agent.id)
    print(f"Total memory items: {len(all_memory)}")

    # Search memory
    print("\nSearching for 'Python'...")
    python_results = await memory_manager.search_memory(agent.id, "Python")
    for item in python_results:
        print(f"  - {item.memory_type.value}: {item.content}")

    # Get memory statistics
    stats = memory_manager.get_memory_stats(agent.id)
    print(f"\nMemory statistics:")
    print(f"  Total items: {stats['total_items']}")
    print(f"  Type counts: {stats['type_counts']}")
    print(f"  Average importance: {stats['average_importance']:.2f}")

    # Get LangChain memory
    langchain_memory = memory_manager.get_langchain_memory(agent.id)
    if langchain_memory:
        variables = langchain_memory.load_memory_variables({})
        print(f"\nLangChain memory variables: {list(variables.keys())}")
        if "history" in variables:
            print(f"Conversation history: {variables['history']}")

    # Add a memory handler
    def memory_handler(memory_item):
        print(
            f"  🔔 Memory handler called: {memory_item.memory_type.value} - {memory_item.content}"
        )

    await memory_manager.add_memory_handler(agent.id, memory_handler)

    # Add another memory to trigger the handler
    print("\nAdding memory with handler...")
    await memory_manager.add_memory(
        agent_id=agent.id,
        memory_type=MemoryType.TASK_RESULT,
        content={"result": "Task completed successfully", "score": 95},
        tags=["result", "success"],
        importance=0.85,
    )

    # Unregister agent (this will save memory to database)
    print("\nUnregistering agent...")
    await memory_manager.unregister_agent(agent.id)
    print("✓ Agent unregistered")

    print("\n=== Example completed ===")


if __name__ == "__main__":
    asyncio.run(main())
