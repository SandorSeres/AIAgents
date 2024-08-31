"""
File Name: human_agent.py
Description: This file defines the HumanAgent class, which simulates a human-like agent within a multi-agent system. The agent manages its memory, can be cloned, and is capable of interacting with other agents or components of the system. It primarily handles message storage and retrieval and is designed to maintain a minimal state, as it does not interact with LLMs or external tools.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [License Type]
"""

from datetime import datetime
import logging
from memory import Memory

class HumanAgent:
    """
    Class Name: HumanAgent
    Description: HumanAgent simulates a human participant in a multi-agent system. This agent manages messages and memory but does not use tools or LLMs. It is primarily used to simulate human interactions or as a placeholder for a real user within the system.

    Attributes:
        name (str): The name of the agent.
        role (str): The role assigned to the agent.
        role_description (str): A description of the agent's role.
        pre_processing_tools (None): Placeholder for consistency with other agent classes; not used in HumanAgent.
        post_processing_tools (None): Placeholder for consistency with other agent classes; not used in HumanAgent.
        memory (Memory): An instance of the Memory class for managing the agent's memory.
    """

    def __init__(self, name, role, role_description):
        """
        Initializes the HumanAgent with the given name, role, and role description.

        Parameters:
            name (str): The name of the agent.
            role (str): The role assigned to the agent.
            role_description (str): A description of the agent's role.
        """
        self.name = name
        self.role = role
        self.role_description = role_description
        self.pre_processing_tools = None
        self.post_processing_tools = None
        self.memory = Memory(name)  # Initialize memory based on agent name
        logging.info(f"Initialized HumanAgent: {self.name}, Role: {self.role}, Description: {self.role_description}")

    def get_state(self):
        """
        Retrieves the current state of the agent, including memory and tool history.

        Returns:
            dict: A dictionary containing the agent's name, role, short-term memory, tool history, and placeholders for tools and LLM.
        """
        state = {
            'name': self.name,
            'role': self.role,
            'short_term_memory': self.memory.get_short_term_memory(),
            'tool_history': self.memory.get_tool_history(),
            'llm': None,
            'pre_processing_tools': [],
            'post_processing_tools': []
        }
        logging.info(f"({self.name}): Current state fetched.")
        return state

    def init_messages(self):
        """
        Initializes the agent's stored messages list, used for simulating message handling.
        """
        self.stored_messages = []
        logging.debug(f"Messages initialized for HumanAgent: {self.name}")

    def update_messages(self, message):
        """
        Updates the agent's short-term memory with a new message.

        Parameters:
            message (str): The message to be added to the short-term memory.

        Returns:
            list: The updated short-term memory.
        """
        self.memory.add_to_short_term(message)
        logging.debug(f"({self.name}): Updated short-term memory: {len(self.memory.get_short_term_memory())}")
        return self.memory.get_short_term_memory()

    def reset(self):
        """
        Resets the agent's messages and reinitializes its message storage.
        """
        self.init_messages()
        logging.info(f"Messages reset for HumanAgent: {self.name}")

    def step(self, input_message):
        """
        Simulates the agent's response to an input message by returning the message as-is.

        Parameters:
            input_message (str): The input message received by the agent.

        Returns:
            str: The same input message, simulating a simple echo behavior.
        """
        return input_message
         
    def clone(self):
        """
        Creates a clone of the current agent, including its memory.

        Returns:
            HumanAgent: A new instance of HumanAgent with the same configuration and memory state.
        """
        cloned_agent = HumanAgent(
            name=self.name,
            role=self.role, 
            role_description=self.role_description
        )
        cloned_agent.memory.short_term_memory = self.memory.get_short_term_memory().copy()
        return cloned_agent

    def end(self):
        """
        Finalizes the agent's session. Currently, this method does nothing, but it can be extended for cleanup operations if needed.
        """
        pass

