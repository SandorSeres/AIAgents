Memory Class Documentation

## Class Overview

### Class Name: `Memory`

The `Memory` class is responsible for managing an AI agent's short-term and long-term memory. It allows for the addition of messages to memory, retrieval of stored messages, and saving/loading of long-term memory from disk. The class also keeps track of the history of tools used by the agent.

### Attributes:
- **short_term_memory (list)**: Stores recent messages with associated priorities.
- **long_term_memory (list)**: Stores important messages for long-term reference.
- **tool_history (list)**: Tracks the history of tools used by the agent.
- **agent_name (str)**: The name of the agent associated with this memory instance.
- **memory_file (str)**: The file path where the agent's memory is stored persistently.

## Function Descriptions

### `__init__(self, agent_name)`
Initializes the Memory instance with the specified agent name, setting up the short-term and long-term memory, and loading any existing long-term memory from a file.

#### Parameters:
- **agent_name (str)**: The name of the agent associated with this memory.

### `add_to_short_term(self, message, priority=1)`
Adds a message to the short-term memory with an optional priority level.

#### Parameters:
- **message (str)**: The message to add to short-term memory.
- **priority (int)**: The priority level of the message (default is 1).

#### Notes:
- Short-term memory is limited to 100 messages. If the limit is exceeded, the oldest message is removed.

### `add_to_long_term(self, message)`
Adds a message to the long-term memory.

#### Parameters:
- **message (str)**: The message to add to long-term memory.

### `add_to_tool_history(self, message)`
Adds a message to the tool history.

#### Parameters:
- **message (str)**: The message related to tool usage to add to the history.

### `get_short_term_memory(self)`
Retrieves the full short-term memory, including messages and their priorities.

#### Returns:
- **list**: A list of dictionaries representing the short-term memory.

### `get_short_term_messages(self)`
Retrieves only the messages from the short-term memory, excluding priority information.

#### Returns:
- **list**: A list of messages stored in short-term memory.

### `get_long_term_memory(self)`
Retrieves the full long-term memory.

#### Returns:
- **list**: A list of messages stored in long-term memory.

### `get_tool_history(self)`
Retrieves the full tool usage history.

#### Returns:
- **list**: A list of messages related to tool usage.

### `reset_short_term(self)`
Resets the short-term memory, clearing all stored messages.

### `load_long_term_memory(self)`
Loads the long-term memory and tool history from a file.

#### Notes:
- If the file does not exist, initializes with an empty list.
- If the file cannot be decoded, initializes with an empty list.

### `save_long_term_memory(self)`
Saves the long-term memory and tool history to a file. The file is stored at a path based on the agent's name.

#### Notes:
- After saving, the short-term memory is reset.

### `filter_combined(self, messages, keywords=None, min_priority=1)`
Filters the provided messages based on specified keywords and minimum priority. Messages matching any keyword or meeting the minimum priority are returned.

#### Parameters:
- **messages (list)**: A list of messages to filter.
- **keywords (list)**: A list of keywords to match in the message content (optional).
- **min_priority (int)**: The minimum priority level to include in the filtered results (default is 1).

#### Returns:
- **list**: A list of filtered messages based on the provided criteria.

#### Logs:
- **Info**: When a message contains matched keywords.

## Detailed Algorithm Explanations

### Memory Management
1. **Initialization**: When an instance of `Memory` is created, it initializes short-term and long-term memory and attempts to load existing long-term memory from a JSON file.
2. **Adding Messages**: Messages can be added to either short-term or long-term memory. Short-term memory has a limit of 100 messages, ensuring that only the most recent messages are retained.
3. **Loading and Saving**: Long-term memory is loaded from a JSON file upon initialization and can be saved back to the file system, ensuring persistence across sessions.

### Filtering Messages
The `filter_combined` method allows for filtering messages based on keywords and priority. It checks each message against the provided criteria and logs any matched keywords.

## Basic Examples

### Creating a Memory Instance
```python
memory = Memory(agent_name="Agent007")
```

### Adding Messages
```python
memory.add_to_short_term("This is a short-term message.", priority=2)
memory.add_to_long_term("This is a long-term message.")
memory.add_to_tool_history("Used tool X.")
```

### Retrieving Messages
```python
short_term = memory.get_short_term_memory()
long_term = memory.get_long_term_memory()
tool_history = memory.get_tool_history()
```

### Filtering Messages
```python
filtered_messages = memory.filter_combined(memory.get_short_term_memory(), keywords=["urgent"], min_priority=1)
```

## Expected Outputs
- Retrieving short-term memory will return a list of messages with their priorities.
- Filtering messages will return only those that match the specified criteria.

This documentation provides a comprehensive overview of the `Memory` class, its methods, and its usage within an AI agent context.
