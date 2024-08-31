Memory Module Documentation

## Overview

The `memory.py` file defines the `Memory` class, which is responsible for managing both short-term and long-term memory for an AI agent. This class supports adding, retrieving, and filtering memories, as well as saving and loading long-term memory from a persistent storage file. It also tracks the history of tools used by the agent.

### Author
- Sandor Seres (sseres@code.hu)

### Date
- 2024-08-31

### Version
- 1.0

### License
- Creative Commons Zero v1.0 Universal

## Class: Memory

### Description
The `Memory` class manages an AI agent's memory, allowing for the addition of messages, retrieval of stored messages, and saving/loading of long-term memory from disk. It also keeps track of the history of tools used by the agent.

### Attributes
- **short_term_memory (list)**: Stores recent messages with associated priorities.
- **long_term_memory (list)**: Stores important messages for long-term reference.
- **tool_history (list)**: Tracks the history of tools used by the agent.
- **agent_name (str)**: The name of the agent associated with this memory instance.
- **memory_file (str)**: The file path where the agent's memory is stored persistently.

### Methods

#### `__init__(self, agent_name)`
Initializes the Memory instance with the specified agent name, setting up the short-term and long-term memory, and loading any existing long-term memory from a file.

**Parameters:**
- `agent_name (str)`: The name of the agent associated with this memory.

#### `add_to_short_term(self, message, priority=1)`
Adds a message to the short-term memory with an optional priority level.

**Parameters:**
- `message (str)`: The message to add to short-term memory.
- `priority (int)`: The priority level of the message (default is 1).

**Notes:**
- Short-term memory is limited to 100 messages. If the limit is exceeded, the oldest message is removed.

#### `add_to_long_term(self, message)`
Adds a message to the long-term memory.

**Parameters:**
- `message (str)`: The message to add to long-term memory.

#### `add_to_tool_history(self, message)`
Adds a message to the tool history.

**Parameters:**
- `message (str)`: The message related to tool usage to add to the history.

#### `get_short_term_memory(self)`
Retrieves the full short-term memory, including messages and their priorities.

**Returns:**
- `list`: A list of dictionaries representing the short-term memory.

#### `get_short_term_messages(self)`
Retrieves only the messages from the short-term memory, excluding priority information.

**Returns:**
- `list`: A list of messages stored in short-term memory.

#### `get_long_term_memory(self)`
Retrieves the full long-term memory.

**Returns:**
- `list`: A list of messages stored in long-term memory.

#### `get_tool_history(self)`
Retrieves the full tool usage history.

**Returns:**
- `list`: A list of messages related to tool usage.

#### `reset_short_term(self)`
Resets the short-term memory, clearing all stored messages.

#### `save_long_term_memory(self)`
Saves the long-term memory and tool history to a file. The file is stored at a path based on the agent's name.

**Notes:**
- After saving, the short-term memory is reset.

#### `load_long_term_memory(self)`
Loads the long-term memory and tool history from a file. If the file does not exist, initializes with empty lists.

#### `filter_combined(self, messages, keywords=None, min_priority=1)`
Filters the provided messages based on specified keywords and minimum priority. Messages matching any keyword or meeting the minimum priority are returned.

**Parameters:**
- `messages (list)`: A list of messages to filter.
- `keywords (list)`: A list of keywords to match in the message content (optional).
- `min_priority (int)`: The minimum priority level to include in the filtered results (default is 1).

**Returns:**
- `list`: A list of filtered messages based on the provided criteria.

**Logs:**
- Info: When a message contains matched keywords.

## Examples

### Basic Usage

```python
# Create a Memory instance for an agent named "Agent007"
memory = Memory(agent_name="Agent007")

# Add messages to short-term memory
memory.add_to_short_term("First short-term message", priority=2)
memory.add_to_short_term("Second short-term message")

# Retrieve short-term messages
short_term_messages = memory.get_short_term_messages()
print(short_term_messages)

# Add a message to long-term memory
memory.add_to_long_term("Important long-term message")

# Save long-term memory to file
memory.save_long_term_memory()

# Load long-term memory from file
memory.load_long_term_memory()
```

### Filtering Messages

```python
# Filter messages with a keyword and minimum priority
filtered_messages = memory.filter_combined(memory.get_short_term_memory(), keywords=["First"], min_priority=1)
print(filtered_messages)
```

## Conclusion

The `Memory` class provides a robust framework for managing an AI agent's memory, ensuring efficient storage and retrieval of both short-term and long-term information while maintaining a history of tool usage.
