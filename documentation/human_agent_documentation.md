Human Agent Module Documentation

## Overview

The `human_agent.py` file defines the `HumanAgent` class, which simulates a human-like agent within a multi-agent system. This agent manages its memory, can be cloned, and is capable of interacting with other agents or components of the system. It primarily handles message storage and retrieval and is designed to maintain a minimal state, as it does not interact with LLMs or external tools.

### Author
- Sandor Seres (sseres@code.hu)

### Date
- 2024-08-31

### Version
- 1.0

### License
- Creative Commons Zero v1.0 Universal

## Class: HumanAgent

### Description
The `HumanAgent` class simulates a human participant in a multi-agent system. This agent manages messages and memory but does not use tools or LLMs. It is primarily used to simulate human interactions or as a placeholder for a real user within the system.

### Attributes
- **name (str)**: The name of the agent.
- **role (str)**: The role assigned to the agent.
- **role_description (str)**: A description of the agent's role.
- **pre_processing_tools (None)**: Placeholder for consistency with other agent classes; not used in `HumanAgent`.
- **post_processing_tools (None)**: Placeholder for consistency with other agent classes; not used in `HumanAgent`.
- **memory (Memory)**: An instance of the `Memory` class for managing the agent's memory.

### Methods

#### `__init__(self, name, role, role_description)`
Initializes the `HumanAgent` with the given name, role, and role description.

**Parameters:**
- `name (str)`: The name of the agent.
- `role (str)`: The role assigned to the agent.
- `role_description (str)`: A description of the agent's role.

#### `get_state(self)`
Retrieves the current state of the agent, including memory and tool history.

**Returns:**
- `dict`: A dictionary containing the agent's name, role, short-term memory, tool history, and placeholders for tools and LLM.

#### `init_messages(self)`
Initializes the agent's stored messages list, used for simulating message handling.

#### `update_messages(self, message)`
Updates the agent's short-term memory with a new message.

**Parameters:**
- `message (str)`: The message to be added to the short-term memory.

**Returns:**
- `list`: The updated short-term memory.

#### `reset(self)`
Resets the agent's messages and reinitializes its message storage.

#### `step(self, input_message)`
Simulates the agent's response to an input message by returning the message as-is.

**Parameters:**
- `input_message (str)`: The input message received by the agent.

**Returns:**
- `str`: The same input message, simulating a simple echo behavior.

#### `clone(self)`
Creates a clone of the current agent, including its memory.

**Returns:**
- `HumanAgent`: A new instance of `HumanAgent` with the same configuration and memory state.

#### `end(self)`
Finalizes the agent's session. Currently, this method does nothing, but it can be extended for cleanup operations if needed.

## Examples

### Basic Usage

```python
# Create a HumanAgent instance
agent = HumanAgent(name="Agent001", role="Simulated User", role_description="A placeholder for human interactions.")

# Initialize messages
agent.init_messages()

# Update messages
agent.update_messages("Hello, how can I help you?")

# Get the current state of the agent
state = agent.get_state()
print(state)

# Simulate a response
response = agent.step("What is your name?")
print(response)

# Clone the agent
cloned_agent = agent.clone()
print(cloned_agent.get_state())
```

## Conclusion

The `HumanAgent` class provides a framework for simulating human-like interactions within a multi-agent system. It effectively manages message storage and retrieval while maintaining a minimal state, making it suitable for testing and simulating user interactions.
