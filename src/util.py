"""
File Name: util.py
Description: This file contains various utility functions and classes used in an AI-based application. These include logging setup, YAML configuration loading, agent creation, cost calculation, and markdown conversion to Facebook format. The utilities support core operations, enabling effective management of agents and their interactions within the system.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

from markdown import markdown
from bs4 import BeautifulSoup
import re
from datetime import datetime
import yaml
import logging
import os
from tools.search_tool import *
from tools.image_generation import ImageGenerationTool
from tools.file_tool import *
from tools.dummy_tool import DummyTool
from tools.git_tool import *
from tools.rag_tools import *
from tools.execute_tool import *
from typing import List
from memory import Memory
from util import *

import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Beállítja az alkalmazás naplózási konfigurációját. A naplók a konzolra és egy forgó fájlba íródnak.
    A formátum tartalmazza az időbélyeget, a napló szintjét, a logger nevét, az üzenetet, valamint a forrásfájlt és a sor számát.
    Legfeljebb 10 naplófájlt tart meg, egyenként maximum 5 MB méretben.
    """
    # Ensure the directory exists
    os.makedirs('./log', exist_ok=True)
    # Forgó fájlkezelő létrehozása
    rotating_handler = RotatingFileHandler(
        "./log/app.log",
        mode='a',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=10,
        encoding='utf-8',
        delay=0
    )

    # Naplózási konfiguráció beállítása
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d',
        handlers=[
            logging.StreamHandler(),  # Konzolra írás
            rotating_handler          # Forgó fájlba írás
        ]
    )

def load_yaml(file_path):
    """
    Loads and parses a YAML configuration file, replacing environment variables.

    Parameters:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The parsed YAML file as a dictionary with environment variables substituted.

    Logs:
        Info: On successful loading of the YAML file.
        Error: If there is an issue loading or parsing the YAML file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Replace environment variables in the content
        content = os.path.expandvars(content)

        config = yaml.safe_load(content)
        logging.info(f"YAML file loaded from {file_path}")
        return config
    except Exception as e:
        logging.error(f"Error loading YAML file from {file_path}: {e}")
        return None
        
def create_agent(role_name, agent_config):
    """
    Creates an agent based on the provided configuration. Supports HumanAgent and CAMELAgent types.

    Parameters:
        role_name (str): The name of the role for the agent.
        agent_config (dict): Configuration details for the agent, including its type and associated tools.

    Returns:
        Object: An instance of the created agent.

    Logs:
        Info: On successful creation of the agent.
        Error: If there is an issue during the creation of the agent.
    """
    try:
        from human_agent import HumanAgent
        from camel_agent import CAMELAgent

        # Extract agent configuration
        agent_type = agent_config['type']

        # Initialize pre-processing tools
        pre_processing_tools = agent_config.get('tools', {}).get('pre-processing', [])
        pre_processed_tool_instances = []
        for tool_name in pre_processing_tools:
            tool_instance = eval(tool_name)()  # Instantiate the tool class
            pre_processed_tool_instances.append(tool_instance)

        # Initialize post-processing tools
        post_processing_tools = agent_config.get('tools', {}).get('post-processing', [])
        post_processed_tool_instances = []
        for tool_name in post_processing_tools:
            tool_instance = eval(tool_name)()  # Instantiate the tool class
            post_processed_tool_instances.append(tool_instance)

        # Create the agent
        if agent_type == 'HumanAgent':
            role_name = agent_config['role_name']
            role_description = agent_config['role_description']
            agent = HumanAgent(
                name=role_name,
                role=role_name, 
                role_description=role_description
            )
        else:  # Default to CAMELAgent
            role_name = agent_config['role_name']
            role_description = agent_config['role_description']
            system_prompt = agent_config['system_prompt']
            sys_msg = {"role": "system", "content": system_prompt}
            agent = CAMELAgent(
                name=role_name,
                role=role_name,
                role_description=role_description,
                system_message=sys_msg,
                llm=agent_config.get('llm', 'openai'),
                pre_processing_tools=pre_processed_tool_instances, 
                post_processing_tools=post_processed_tool_instances
            )

        logging.info(f"Agent created: {role_name} of type {agent_type}")
        return agent
    except Exception as e:
        logging.error(f"Error creating agent {role_name}: {e}", exc_info=True)

import json
import logging

def extract_json_string(text: str) -> str:
    """
    Extracts a JSON string from a block of text.

    Parameters:
        text (str): The text containing the JSON string.

    Returns:
        str: The extracted JSON string, or an empty JSON object/list if extraction fails.

    Logs:
        Warning: If there is an error during JSON extraction.
    """
    def find_matching_end(text, start_pos, open_char, close_char):
        stack = 1
        for i in range(start_pos + 1, len(text)):
            if text[i] == open_char:
                stack += 1
            elif text[i] == close_char:
                stack -= 1
                if stack == 0:
                    return i + 1
        return -1  # No matching closing character found

    try:
        # Find the first occurrence of '{' or '['
        first_brace = text.find('{')
        first_bracket = text.find('[')

        if first_brace == -1 and first_bracket == -1:
            raise ValueError("No JSON object or array found in the text.")

        if first_brace == -1:
            start = first_bracket
            open_char = '['
            close_char = ']'
        elif first_bracket == -1:
            start = first_brace
            open_char = '{'
            close_char = '}'
        else:
            if first_brace < first_bracket:
                start = first_brace
                open_char = '{'
                close_char = '}'
            else:
                start = first_bracket
                open_char = '['
                close_char = ']'

        end = find_matching_end(text, start, open_char, close_char)
        if end == -1:
            raise ValueError("No matching closing character found for JSON.")

        json_str = text[start:end]
        return json_str

    except Exception as e:
        logging.warning(f"JSON extraction error: {e}; text: {text}")
        # Determine what to return based on the first opening character
        if 'open_char' in locals():
            if open_char == '{':
                return "{}"
            elif open_char == '[':
                return "[]"
        return "{}"  # Default to empty JSON object


def parse_user_instruction(instruction):
    """
    Parses a user instruction, extracting and returning the JSON content.

    Parameters:
        instruction (str): The instruction text containing JSON data.

    Returns:
        dict: The parsed JSON data.

    Logs:
        Info: On successful parsing of the user instruction.
        Warning: If there is an error during JSON parsing.
    """
    try:
        json_data = json.loads(extract_json_string(instruction))
        logging.info(f"User instruction parsed successfully: {json_data}")
        return json_data
    except json.JSONDecodeError as e:
        logging.warning(f"Error parsing user instruction: {e}: {instruction}")
        return {}

def calculate_costs(usage_metrics, model_input_price, model_output_price, unit_of_tokens):
    """
    Calculates and logs the cost of an AI model's usage based on token consumption.

    Parameters:
        usage_metrics (object): The usage metrics object containing token counts.
        model_input_price (float): The cost per unit of input tokens.
        model_output_price (float): The cost per unit of output tokens.
        unit_of_tokens (int): The number of tokens per unit for pricing.

    Logs:
        Info: When costs are successfully calculated and saved.
        Error: If there is an issue during cost calculation.
    """
    try:
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        cost = usage_metrics.to_dict()
        cost["Time"] = current_time

        prompt_tokens = cost['prompt_tokens']
        completion_tokens = cost['completion_tokens']
        
        input_cost = (prompt_tokens / unit_of_tokens) * model_input_price
        cost["input_cost"] = input_cost
        output_cost = (completion_tokens / unit_of_tokens) * model_output_price
        cost["output_cost"] = output_cost
        cost["total_cost"] = input_cost + output_cost

        with open("camel_cost.csv", "a") as cost_file:
            print(cost, file=cost_file)
        logging.info(f"Costs calculated and saved at {current_time}.")
    except Exception as e:
        logging.error(f"Error calculating costs: {e}")

def markdown_to_facebook(text):
    """
    Converts markdown text to a format suitable for posting on Facebook, handling various HTML elements and formatting.

    Parameters:
        text (str): The markdown text to be converted.

    Returns:
        str: The text converted to Facebook format.

    Logs:
        Info: When the conversion is successful.
        Error: If there is an issue during the conversion process.
    """
    try:
        # Convert markdown to HTML
        html = markdown(text)
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Convert HTML elements to Facebook formatted text
        facebook_text = ''
        for element in soup.descendants:
            if element.name == 'h1':
                facebook_text += f'\n# {element.get_text()}\n'
            elif element.name == 'h2':
                facebook_text += f'\n## {element.get_text()}\n'
            elif element.name == 'h3':
                facebook_text += f'\n### {element.get_text()}\n'
            elif element.name == 'strong':
                facebook_text += f'**{element.get_text()}**'
            elif element.name == 'em':
                facebook_text += f'*{element.get_text()}*'
            elif element.name == 'ul':
                facebook_text += '\n'
            elif element.name == 'li':
                facebook_text += f'- {element.get_text()}\n'
            elif element.name == 'a':
                facebook_text += f'[{element.get_text()}]({element.get("href")})'
            elif element.name is None:
                facebook_text += element

        # Remove any extra newlines or spaces
        facebook_text = re.sub(r'\n{2,}', '\n', facebook_text).strip()
        
        logging.info("Markdown converted to Facebook format successfully.")
        return facebook_text
    except Exception as e:
        logging.error(f"Error converting markdown to Facebook format: {e}")
        return ""

