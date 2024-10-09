import json
import os
import logging
import asyncio

class Memory:
    """
    Class Name: Memory
    Description: The Memory class is responsible for managing an AI agent's short-term and long-term memory. It allows for the addition of messages to memory, retrieval of stored messages, and saving/loading of long-term memory from disk. The class also keeps track of the history of tools used by the agent.

    Attributes:
        short_term_memory (list): Stores recent messages with associated priorities.
        long_term_memory (list): Stores important messages for long-term reference.
        tool_history (list): Tracks the history of tools used by the agent.
        agent_name (str): The name of the agent associated with this memory instance.
        memory_file (str): The file path where the agent's memory is stored persistently.
    """

    def __init__(self, agent_name):
        """
        Initializes the Memory instance with the specified agent name, setting up the short-term and long-term memory, and loading any existing long-term memory from a file.

        Parameters:
            agent_name (str): The name of the agent associated with this memory.
        """
        self.short_term_memory = []
        self.long_term_memory = []
        self.tool_old_history = []
        self.tool_history = []
        self.name = agent_name
        # Ensure the directory exists
        os.makedirs('./memories', exist_ok=True)
        self.memory_file = f"./memories/{agent_name}_memory.json"
        self.load_long_term_memory()

    def add_to_short_term(self, message, priority=1):
        """
        Adds a message to the short-term memory with an optional priority level.

        Parameters:
            message (str): The message to add to short-term memory.
            priority (int): The priority level of the message (default is 1).

        Notes:
            - Short-term memory is limited to 100 messages. If the limit is exceeded, the oldest message is removed.
        """
        self.short_term_memory.append({'message': message, 'priority': priority})
        if len(self.short_term_memory) > 100:  # Optional limit for short-term memory
            self.short_term_memory.pop(0)

    def remove_top_of_short_term(self):
        """
        Removes the last item added to the short-term memory.
        """
        if self.short_term_memory:
            removed_item = self.short_term_memory.pop()
            logging.info(f"Removed last element from short-term memory")
        else:
            logging.warning("Short-term memory is already empty.")

    def add_to_long_term(self, message):
        """
        Adds a message to the long-term memory.

        Parameters:
            message (str): The message to add to long-term memory.
        """
        self.long_term_memory.append(message)

    def add_to_tool_history(self, message):
        """
        Adds a message to the tool history.

        Parameters:
            message (str): The message related to tool usage to add to the history.
        """
        self.tool_history.append(message)

    def get_short_term_memory(self):
        """
        Retrieves the full short-term memory, including messages and their priorities.

        Returns:
            list: A list of dictionaries representing the short-term memory.
        """
        return self.short_term_memory

    def get_short_term_messages(self):
        """
        Retrieves only the messages from the short-term memory, excluding priority information.

        Returns:
            list: A list of messages stored in short-term memory.
        """
        return [item['message'] for item in self.short_term_memory]

    def get_long_term_memory(self):
        """
        Retrieves the full long-term memory.

        Returns:
            list: A list of messages stored in long-term memory.
        """
        return self.long_term_memory

    def get_tool_history(self):
        """
        Retrieves the full tool usage history.

        Returns:
            list: A list of messages related to tool usage.
        """
        return self.tool_history

    def reset_short_term(self):
        """
        Resets the short-term memory, clearing all stored messages.
        """
        self.short_term_memory = []

    def load_long_term_memory(self):
        """
        Loads the long-term memory and tool history from a file.

        Notes:
            - If the file does not exist, initializes with an empty list.
            - If the file cannot be decoded, initializes with an empty list.
        """
        try:
            with open(self.memory_file, "r") as file:
                data = json.load(file)
                self.long_term_memory = data.get('long_term_memory', [])
                #  nem kell a sessionhoz a régi tool használat
                self.tool_old_history = data.get('tool_history', [])
            self.tool_history = []
            logging.info(f"Memory loaded successfully from {self.memory_file}")
        except FileNotFoundError:
            logging.warning(f"No previous memory file found for {self.memory_file}, starting fresh.")
            self.long_term_memory = []
            self.tool_history = []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from memory file: {e}")
            self.long_term_memory = []
            self.tool_history = []

    def save_long_term_memory(self):
        """
        Saves the long-term memory and tool history to a file. The file is stored at a path based on the agent's name.

        Notes:
            - After saving, the short-term memory is reset.
        """
        data = {
            "long_term_memory": self.long_term_memory,
            "tool_history": self.tool_old_history + self.tool_history
        }
        try:
            # Ellenőrizze a data tartalmát és szűrje ki a nem sorozható objektumokat
            def is_serializable(value):
                try:
                    json.dumps(value)
                    return True
                except (TypeError, ValueError):
                    return False

            # Szűrés a mentendő adatokon
            serializable_data = {k: v for k, v in data.items() if is_serializable(v)}

            with open(self.memory_file, "w") as file:
                json.dump(serializable_data, file, indent=4)
            logging.info(f"Memory saved successfully to {self.memory_file}")
        
        except Exception as e:
            logging.error(f"Error saving long-term memory: {e}", exc_info=True)

    def filter_combined(self, messages, keywords=None, min_priority=1):
        """
        Filters the provided messages based on specified keywords and minimum priority. Messages matching any keyword or meeting the minimum priority are returned.

        Parameters:
            messages (list): A list of messages to filter.
            keywords (list): A list of keywords to match in the message content (optional).
            min_priority (int): The minimum priority level to include in the filtered results (default is 1).

        Returns:
            list: A list of filtered messages based on the provided criteria.

        Logs:
            Info: When a message contains matched keywords.
        """
        filtered = []
        for item in messages:
            matched_keywords = []  # List for found keywords
            if keywords:
                # Check if any of the keywords are found in the message content
                for keyword in keywords:
                    if keyword in item['message']['content']:
                        matched_keywords.append(keyword)  # Add found keyword
                if matched_keywords:
                    logging.info(matched_keywords)
                    filtered.append(item['message'])
                    continue  # Skip to the next message if a match is found
            # Check for priority
            if item['priority'] >= min_priority:
                filtered.append(item['message'])
        return filtered
