"""
File Name: camel_agent.py
Description: This file defines the CAMELAgent class, which serves as an AI agent capable of interacting with various tools and LLMs (Large Language Models) like OpenAI and RunPod. The agent manages memory, executes tasks with pre-processing and post-processing tools, and handles complex interactions with external APIs. It is designed for use in multi-agent systems where it can autonomously manage tasks and respond to user input.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import logging
from tools.execute_tool import RunPythonTool
from tools.search_tool import SearchAndRetrieveTool
from tools.image_generation import ImageGenerationTool
from tools.file_tool import ReadFileTool, SaveToFileTool
from tools.dummy_tool import DummyTool
import openai
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import time
import os
import re
from memory import Memory
from jsonschema import validate, ValidationError
import asyncio

# Priority levels for message handling
LOW_PRIORITY = 1
MEDIUM_PRIORITY = 2
HIGH_PRIORITY = 3

class CAMELAgent:
    """
    Class Name: CAMELAgent
    Description: CAMELAgent is an AI agent designed to interact with different LLMs (like OpenAI and RunPod) and tools to perform tasks autonomously.
                 The agent can execute tasks by utilizing pre-processing and post-processing tools, manage memory, and interact with external APIs.
                 It is primarily used in complex multi-agent systems for managing and executing various roles.

    Attributes:
        name (str): The name of the agent.
        role (str): The role assigned to the agent.
        role_description (str): A description of the agent's role.
        system_message (str): The initial system message that the agent uses as a starting point.
        llm (str): The type of Large Language Model used by the agent (e.g., "openai" or "runpod").
        memory (Memory): An instance of the Memory class for managing the agent's memory.
        pre_processing_tools (list): A list of tools used for pre-processing tasks.
        post_processing_tools (list): A list of tools used for post-processing tasks.
        client (object): The client object for interacting with the chosen LLM (e.g., OpenAI API).
        END_POINT (str): The endpoint for RunPod API (only if llm is "runpod").
        BASE_URL (str): The base URL for the RunPod API (only if llm is "runpod").
        headers (dict): Headers for authenticating requests to the RunPod API (only if llm is "runpod").
    """

    def __init__(self, name, role, role_description, system_message, llm="openai", pre_processing_tools=[], post_processing_tools=[]):
        """
        Initializes the CAMELAgent with the given parameters, including setting up the memory and tools.

        Parameters:
            name (str): The name of the agent.
            role (str): The role assigned to the agent.
            role_description (str): A description of the agent's role.
            system_message (str): The initial system message used to start the agent's context.
            llm (str): The type of Large Language Model to use (default is "openai").
            pre_processing_tools (list): List of tools for pre-processing.
            post_processing_tools (list): List of tools for post-processing.
        """
        self.name = name
        self.role = role
        self.role_description = role_description
        self.system_message = system_message
        self.llm = llm
        self.memory = Memory(name)  # Initialize memory based on agent name
        self.pre_processing_tools = pre_processing_tools
        self.post_processing_tools = post_processing_tools
        
        if llm == "openai":
            self.client = openai.OpenAI()
        elif llm == "runpod":
            self.END_POINT = os.getenv("END_POINT")
            self.BASE_URL = f"https://api.runpod.ai/v2/{self.END_POINT}/openai/v1"
            self.headers = {"Authorization": f"Bearer {os.getenv('RUNPOD_API_KEY')}"}
        
        logging.info(f"({self.name}): Initialized CAMELAgent with LLM: {self.llm} and tools: {[tool.name for tool in (self.pre_processing_tools + self.post_processing_tools)]}")

    def get_state(self):
        """
        Retrieves the current state of the agent, including memory and tool history.

        Returns:
            dict: A dictionary containing the agent's name, role, short-term memory, tool history, LLM type, and tools.
        """
        state = {
            'name': self.name,
            'role': self.role,
            'short_term_memory': self.memory.get_short_term_memory(),
            'tool_history': self.memory.get_tool_history(),
            'llm': self.llm,
            'pre_processing_tools': [tool.name for tool in self.pre_processing_tools],
            'post_processing_tools': [tool.name for tool in self.post_processing_tools]
        }
        logging.info(f"({self.name}): Current state fetched.")
        return state

    def reset(self):
        """
        Resets the agent's short-term memory and reinitializes messages with the system message.
        """
        self.memory.reset_short_term()
        self.init_messages()

    def init_messages(self):
        """
        Initializes the agent's messages by adding the system message to the short-term memory with low priority.
        """
        self.memory.add_to_short_term(self.system_message, LOW_PRIORITY)
        logging.info(f"({self.name}): Messages initialized with system message.")
    
    def update_messages(self, message, priority):
        """
        Updates the agent's short-term memory with a new message, ensuring that the message content does not exceed 64k characters.

        Parameters:
            message (dict): The message to be added.
            priority (int): The priority level of the message.
        
        Returns:
            list: The updated short-term memory.
        """
        if asyncio.iscoroutine(message['content']):
            raise TypeError("Coroutines should be awaited before passing to update_messages.")
        
        if len(message['content']) > 64000:
            message['content'] = message['content'][:64000]  # Truncate the message content if too large
        self.memory.add_to_short_term(message, priority=priority)
        logging.debug(f"({self.name}): Updated short-term memory: {len(self.memory.get_short_term_memory())}")
        return self.memory.get_short_term_memory()
        
    def update_tool_history(self, message):
        """
        Updates the tool history in the agent's memory with a new message.

        Parameters:
            message (str): The message to be added to the tool history.
        
        Returns:
            list: The updated tool history.
        """
        self.memory.add_to_tool_history({'role': 'user', 'content': message})
        logging.debug(f"({self.name}): Updated tool history: {len(self.memory.get_tool_history())}")
        return self.memory.get_tool_history()

    def validate_message_structure(self, message):
        """
        Validates the structure of a message to ensure it meets the required format.

        Parameters:
            message (dict): The message to validate.

        Raises:
            ValueError: If the message structure is invalid.
        """
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary.")
        if 'role' not in message or 'content' not in message:
            raise ValueError("Message must contain 'role' and 'content' keys.")
        if not isinstance(message['role'], str) or not isinstance(message['content'], str):
            raise ValueError("'role' and 'content' must be strings.")
        logging.info(f"Message structure validated: {message}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), retry=retry_if_exception_type(openai.OpenAIError))
    async def query_openai(self, messages, max_response_tokens=32000):
        """
        Queries the OpenAI API with the given messages, using retries for reliability.

        Parameters:
            messages (list): A list of messages to send to the OpenAI API.
            max_response_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The content of the response message.
        
        Raises:
            openai.OpenAIError: If an error occurs during the API call.
        """
        from util import calculate_costs
        logging.info(f"({self.name}): Querying OpenAI...")
        try:
            completion = self.client.chat.completions.create(
                messages=messages,
                model=os.getenv("MODEL"),
                temperature=int(os.getenv("TEMPERATURE")),
            )
            calculate_costs(completion.usage, 5, 15, 1000000)
            logging.info(f"({self.name}): OpenAI query successful.")
            return completion.choices[0].message.content
        except openai.OpenAIError as e:
            logging.error(f"({self.name}): OpenAIError: {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), retry=retry_if_exception_type(openai.OpenAIError))
    async def query_openai_with_function_call(self, messages, max_response_tokens=32000):
        """
        Queries the OpenAI API with function call capability, using retries for reliability.

        Parameters:
            messages (list): A list of messages to send to the OpenAI API.
            max_response_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The content of the response message, which may include a function call.
        
        Raises:
            openai.OpenAIError: If an error occurs during the API call.
        """
        from util import calculate_costs
        logging.info(f"({self.name}): Querying OpenAI with function call...")
        try:
            completion = self.client.chat.completions.create(
                messages=messages,
                model=os.getenv("MODEL"),
                # Replace with the actual model
                temperature=int(os.getenv("TEMPERATURE")),
                functions=[
                    {
                        "name": "select_tool",
                        "description": "Selects the appropriate tool and parameters",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "tool": {
                                    "type": "string",
                                    "description": "The name of the tool to use"
                                },
                                "parameters": {
                                    "type": "object",
                                    "description": "The parameters for the tool"
                                }
                            },
                            "required": ["tool"]
                        }
                    }
                ]
            )
            calculate_costs(completion.usage, 5, 15, 1000000)
            logging.info(f"({self.name}): OpenAI query with function call successful.")
            logging.info(f"Tool decision: {completion.choices[0].message.content}")
            return completion.choices[0].message.content
        except openai.OpenAIError as e:
            logging.error(f"({self.name}): OpenAIError: {e}", exc_info=True)
            raise

    def get_response_runpod(self, txt_input):
        """
        Sends a request to the RunPod API and retrieves the response.

        Parameters:
            txt_input (str): The input text to send to the RunPod API.

        Returns:
            dict: The JSON response from the RunPod API.
        """
        url = f"{self.BASE_URL}/run"
        data = {"input": {"message": txt_input}}
        logging.info(f"({self.name}): Querying Runpod...")

        while True:
            try:
                response = requests.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                logging.error(f"({self.name}): RequestException: {e}", exc_info=True)
                logging.info(f"({self.name}): Retrying Runpod run...")
                time.sleep(1)

        return response.json()

    def get_answer_runpod(self, input_message):
        """
        Retrieves the final answer from the RunPod API after polling for completion.

        Parameters:
            input_message (str): The input message for which to get the answer.

        Returns:
            str: The output from the RunPod API or 'FAILED' if the job fails.
        """
        response = self.get_response_runpod(input_message)
        job_id = response.get("id")
        while True:
            try:
                status_response = requests.post(f"{self.BASE_URL}/status/{job_id}", headers=self.headers)
                status_response.raise_for_status()
                status_data = status_response.json()
                output = status_data.get("output")
                if output is not None:
                    return output
                status = status_data.get("status")
                if status == "FAILED":
                    logging.error(f"({self.name}): Runpod job failed.")
                    return 'FAILED'
                logging.info(f"({self.name}): {job_id} Waiting for response... {status}")
                time.sleep(1)
            except requests.RequestException as e:
                logging.error(f"({self.name}): RequestException: {e}", exc_info=True)
                logging.info(f"({self.name}): Retrying Runpod status query...")
                time.sleep(1)

    def query_runpod(self, messages, max_response_tokens=32000):
        """
        Queries the RunPod API with the provided messages.

        Parameters:
            messages (list): A list of messages to send to the RunPod API.
            max_response_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The final response from the RunPod API.
        """
        input_message = messages[-1]['content']
        return self.get_answer_runpod(input_message)

    async def query(self, messages, max_response_tokens=32000):
        """
        Queries the configured LLM (either OpenAI or RunPod) with the provided messages.

        Parameters:
            messages (list): A list of messages to send to the LLM.
            max_response_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The response from the LLM.
        """
        if self.llm == "openai":
            return self.query_openai(messages, max_response_tokens)
        elif self.llm == "runpod":
            return self.query_runpod(messages, max_response_tokens)

    def fix_json(self, json_string):
        """
        Attempts to fix common JSON formatting issues in a string.

        Parameters:
            json_string (str): The JSON string to fix.

        Returns:
            str: The corrected JSON string.
        """
        # Replace single quotes with double quotes
        json_string = re.sub(r"(?<!\\)'", r'"', json_string)
        
        # Add missing commas between objects
        json_string = re.sub(r'}\s*{', '},{', json_string)
        
        # Handle spacing issues with brackets and braces
        json_string = re.sub(r'\s*{\s*', '{', json_string)
        json_string = re.sub(r'\s*}\s*', '}', json_string)
        json_string = re.sub(r'\s*\[\s*', '[', json_string)
        json_string = re.sub(r'\s*\]\s*', ']', json_string)
        
        # Remove trailing commas before closing braces/brackets
        json_string = re.sub(r',\s*([\]}])', r'\1', json_string)
        
        # Balance braces and brackets
        open_braces = json_string.count('{')
        close_braces = json_string.count('}')
        open_brackets = json_string.count('[')
        close_brackets = json_string.count(']')
        
        json_string += '}' * (open_braces - close_braces)
        json_string += ']' * (open_brackets - close_brackets)
        
        return json_string

    def is_valid_json(self, json_string):
        """
        Checks if a given string is valid JSON.

        Parameters:
            json_string (str): The JSON string to validate.

        Returns:
            bool: True if the string is valid JSON, False otherwise.
        """
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False

    def auto_fix_json(self, json_string):
        """
        Automatically attempts to fix JSON formatting issues and checks its validity.

        Parameters:
            json_string (str): The JSON string to fix.

        Returns:
            str or None: The fixed JSON string if valid, or None if it cannot be fixed.
        """
        fixed_json = self.fix_json(json_string)
        if self.is_valid_json(fixed_json):
            return fixed_json
        return None  # Return None if unable to fix

    async def get_tool(self, messages, tools, max_retries=5, delay=2):
        """
        Determines the appropriate tool to use based on the conversation context.

        Parameters:
            messages (list): A list of messages representing the conversation history.
            tools (list): A list of available tools.
            max_retries (int): The maximum number of retries to get a valid tool decision.
            delay (int): The delay in seconds between retries.

        Returns:
            dict or str: A dictionary containing the tool decision, or a string if no tool is needed.
        """
        logging.info(f"Tools: {tools}")
        tool_descriptions = "\n".join(
            [f"{tool.name}: {{ \"description\": \"{tool.description}\", \"parameters\": {tool.parameters} }}" for tool in tools]
        )
        prompt = f"""
        Here are the available tools:
        {tool_descriptions}

        Based on the following conversation, decide which tool to use and with what parameters:

        Conversation:
        {messages[-1]['content']}

        Previous tool history:
        {" ".join([str(message['content']) for message in self.memory.get_tool_history()])}

        Reply with the tool name and parameters to use in JSON format. If no tool is needed, reply with "No tool needed". 

        Example:
        {{ "tool": "Toolname", "parameters": {{"parameter1": "value1", "parameter2": "value2"}} }}
        
        If a new tool is needed, and ONLY if the 'RunPythonTool' is in the tools list, then
        provide the necessary Python code snippet to execute to get the needed output.
        Be very careful and ONLY provide robust production ready code! Include all the needed imports also. The result all the time should be in a <output> variable     
        Example1:
        ```python
        urls = [
            'https://en.wikipedia.org/wiki/Daniel_Kahneman',
            'https://en.wikipedia.org/wiki/Keith_Stanovich',
            ]
        # Function to extract information from a URL
        from bs4 import BeautifulSoup
        import requests
        def extract_info(url):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            text =' '.join([para.text for para in paragraphs])
            return text
        # Gather information from each URL
        output = {{url: extract_info(url) for url in urls}}
        output
        ```
        Example 2:
        ```python
        import openai
        def create_image(text, image_style):
            client = openai.Client()
            prompt = f"{{text}} using the style {{image_style}}"
            print("Image generation prompt:", prompt)
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            output = response['data'][0]['url']
            return output
        ```
        """
        
        attempt = 0
        while attempt < max_retries:
            response = await self.query_openai_with_function_call([{"role": "system", "content": prompt}])
            if response == None:
                response = "No tool needed" 
            if "no tool needed" in response.strip().lower():
                return response.strip()
            
            json_string = self.extract_json_string(response)
            if self.is_valid_json(json_string):
                return json.loads(json_string)
            
            fixed_json = self.auto_fix_json(json_string)
            if fixed_json:
                return json.loads(fixed_json)
            
            logging.warning(f"Received invalid JSON. Cannot fix it: {json_string}. Asking OpenAI to correct it.")
            
            correction_prompt = f"""
            The JSON you provided is invalid. Please correct the following JSON:

            Invalid JSON:
            {json_string}

            Correct the JSON and reply with a valid JSON format.
            """
            
            correction_response = await self.query_openai_with_function_call([{"role": "system", "content": correction_prompt}])
            if isinstance(correction_response, dict):
                correction_content = correction_response.get('content', '')
            else:
                correction_content = correction_response

            if correction_content == None:
                correction_content = "No tool needed"
            if "no tool needed" in correction_content.strip().lower():
                return correction_content.strip()

            corrected_json_string = self.extract_json_string(correction_content)
            
            if self.is_valid_json(corrected_json_string):
                return json.loads(corrected_json_string)
            
            attempt += 1
            logging.warning(f"Correction attempt {attempt} failed. Retrying in {delay} seconds...")
            time.sleep(delay)  # Delay before retrying
        
        logging.error(f"Failed to get a valid JSON response after {max_retries} attempts.")
        return json.loads("{}")  # Return empty JSON if still unable to get a valid response

    def extract_json_string(self, text):
        """
        Extracts a JSON string from a block of text.

        Parameters:
            text (str): The text containing the JSON string.

        Returns:
            str: The extracted JSON string.
        """
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return text[start:end]
        except ValueError:
            logging.warning(f"JSON extraction error: text: {text}")
            return "{}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), retry=retry_if_exception_type(Exception))
    async def use_tool(self, messages, tools):
        """
        Executes a tool based on the decision made from the conversation context.

        Parameters:
            messages (list): A list of messages representing the conversation history.
            tools (list): A list of available tools.

        Returns:
            tuple: A tuple containing the follow-up message and a boolean indicating task completion.
        """
        if not tools:
            logging.info(f"({self.name}): No tools available.")
            return None, True

        tool_decision = self.get_tool(messages, tools)
        logging.info(f"({self.name}): Tool decision: {tool_decision}")

        if tool_decision == None:
            tool_decision = "No tool needed"
        if tool_decision and "no tool needed" in tool_decision.strip().lower():
            return None, True

        try:
            tool_decision = json.loads(self.extract_json_string(tool_decision))
            tool_name = tool_decision['tool']
            params = tool_decision['parameters']

            for tool in tools:
                if tool.name == tool_name:
                    try:
                        if isinstance(params, dict):
                            result, task_completed = tool._run(**params)
                        else:
                            result, task_completed = tool._run(params)

                        if task_completed:
                            follow_up_message = {'role': 'user', 'content': str(result)}
                            return follow_up_message, task_completed

                        if tool.name == "RunPythonTool":
                            for attempt in range(3):
                                error_message = (
                                    "I am providing the following Python code and error message:\n\n"
                                    "Code:\n"
                                    f"{params}\n\n"
                                    "Error Message:\n"
                                    f"{result}\n\n"
                                    "Please suggest a fix for the code to resolve the error."
                                )
                                logging.warning(f"({self.name}): {error_message}")
                                
                                history_context = "\n\n".join([entry['content'] for entry in self.memory.get_tool_history()])
                                detailed_error_message = f"{error_message}\n\nPrevious Attempts:\n{history_context}"
                                self.update_tool_history({'role': 'user', 'content': detailed_error_message})

                                fix_suggestion = self.query([{'role': 'user', 'content': detailed_error_message}])
                                if "Exception" in fix_suggestion:
                                    logging.warning(f"({self.name}): Retrying due to exception in fix suggestion: {fix_suggestion}")
                                    time.sleep(5)
                                else:
                                    result = self.query([{'role': 'system', 'content': fix_suggestion}])
                                    logging.info(f"({self.name}): Tool fix suggestion applied: {result}")
                                    break
                            else:
                                logging.error(f"({self.name}): Failed to fix tool execution after multiple attempts.")
                                return {"error": "Failed to fix the tool execution."}, True
                    except Exception as e:
                        logging.error(f"({self.name}): Tool execution error: {e}", exc_info=True)
                        return {"error": "Tool execution failed."}, True
        except Exception as e:
            logging.error(f"({self.name}): Tool decision processing error: {e}", exc_info=True)
            return {"error": "Tool decision processing failed."}, True

        return None, True

    async def react_prompt(self, input_message):
        """
        Processes an input message, applies pre-processing tools, queries the LLM, and applies post-processing tools.

        Parameters:
            input_message (dict): The input message to process.

        Returns:
            str or dict: The output message after processing, or an error message.
        """
        self.update_messages(input_message, LOW_PRIORITY)

        output_message = None

        if self.pre_processing_tools:
            tool_decision = await self.get_tool(self.memory.get_short_term_messages(), self.pre_processing_tools)
            if isinstance(tool_decision, str):
                tool_decision = None

            if tool_decision:
                tool_name = tool_decision.get('tool')
                params = tool_decision.get('parameters')

                for tool in self.pre_processing_tools:
                    if tool.name == tool_name:
                        try:
                            tool_result, task_completed = tool._run(**params)
                            if task_completed:
                                self.update_tool_history({'role': 'user', 'content': tool_result})
                                self.update_messages({'role': 'user', 'content': tool_result}, MEDIUM_PRIORITY)
                                break
                        except Exception as e:
                            logging.error(f"({self.name}): Error applying pre-processing tool {tool_name}: {e}", exc_info=True)
                            return {"error": "Error applying pre-processing tool."}, True

        output_message = await self.query(self.memory.get_short_term_messages())

        if asyncio.iscoroutine(output_message):
            output_message = await output_message

        self.update_messages({'role': 'user', 'content': output_message}, HIGH_PRIORITY)

        if self.post_processing_tools:
            tool_decision = await self.get_tool(self.memory.get_short_term_messages(), self.post_processing_tools)
            if isinstance(tool_decision, str):
                tool_decision = None

            if tool_decision:
                try:
                    tool_name = tool_decision.get('tool')
                    params = tool_decision.get('parameters')

                    for tool in self.post_processing_tools:
                        if tool.name == tool_name:
                            try:
                                tool_result, task_completed = tool._run(**params)
                                if task_completed:
                                    output_message += tool_result
                                    self.update_tool_history({'role': 'user', 'content': tool_result})
                                    self.update_messages({'role': 'user', 'content': tool_result}, MEDIUM_PRIORITY)
                                    break
                            except Exception as e:
                                logging.error(f"({self.name}): Error applying post-processing tool {tool_name}: {e}", exc_info=True)
                                return {"error": "Error applying post-processing tool."}, True
                except Exception as e:
                    logging.error(f"({self.name}): Tool decision processing error: {e}", exc_info=True)
                    return {"error": "Tool decision processing failed."}, True

        return output_message
                
    async def step(self, input_message):
        """
        Executes a single step in the agent's task sequence by processing the input message and generating a response.

        Parameters:
            input_message (dict): The input message for the current step.

        Returns:
            str or dict: The response generated by the agent, or an error message.
        """
        response = await self.react_prompt(input_message)
        if isinstance(response, (str, dict)):
            return response
        else:
            logging.error(f"({self.name}): Invalid response format: {response}")
            return {"error": "Invalid response format."}

    def clone(self):
        """
        Creates a clone of the current agent, including memory and tool configurations.

        Returns:
            CAMELAgent: A new instance of CAMELAgent with the same configuration and memory state.
        """
        cloned_agent = CAMELAgent(self.name, self.role, self.role_description, self.system_message, self.llm)
        cloned_agent.memory.short_term_memory = self.memory.get_short_term_memory().copy()
        cloned_agent.pre_processing_tools = [tool.clone() for tool in self.pre_processing_tools]
        cloned_agent.post_processing_tools = [tool.clone() for tool in self.post_processing_tools]
        return cloned_agent

    async def summarize_data_with_llm(self, messages):
        """
        Summarizes a set of messages using the LLM.

        Parameters:
            messages (list): A list of messages to summarize.

        Returns:
            dict: A dictionary containing the summarized text.
        """
        text_data = " ".join([item['content'] for item in messages])
        sys_msg = """
            You are a tool for summarizing and abstracting text.
            Return the summarized text to less than 2000 words using markdown format.
            The generated summary should be in the same language as the original text.
            """
        if self.llm == "openai":
            summary = await self.query_openai([{'role': 'system', 'content': f"{sys_msg}: {text_data}"}])
        elif self.llm == "runpod":
            summary = self.query_runpod([{'role': 'system', 'content': f"{sys_msg}: {text_data}"}])
        return {'role': 'system', 'content': summary}

    async def end(self):
        """
        Finalizes the agent's session by transferring relevant messages from short-term memory to long-term memory with summarization.
        """
        keyword = ["Question", "Solution", "Instruction"]
        min_priority = 10

        filtered_messages = self.memory.filter_combined(self.memory.get_short_term_memory(), keyword, min_priority)
        
        if filtered_messages:
            summarized_message = self.summarize_data_with_llm(filtered_messages)
            self.memory.add_to_long_term(summarized_message)
        
        self.memory.save_long_term_memory()

        logging.info(f"({self.name}): Transferred short-term memory to long-term memory with filters and summarization.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    agent_config = {
        'type': 'CAMELAgent',
        'role_name': 'example_agent',
        'role_description': 'An example agent for demonstration.',
        'system_prompt': 'You are an example agent.',
        'tools': {
            'pre-processing': ['SomePreProcessingTool'],
            'post-processing': ['SomePostProcessingTool'],
            'SomePreProcessingTool': 'PreProcessingToolClass',
            'SomePostProcessingTool': 'PostProcessingToolClass'
        },
        'llm': 'openai'
    }

    from util import *
    agent = create_agent('example_role', agent_config)
    
    input_message = {'role': 'user', 'content': 'What is the weather like today?'}

    response = agent.step(input_message)
    print(response)

