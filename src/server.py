"""
File Name: main.py
Description: This file serves as the orchestration layer for a multi-agent AI solution. It handles the initialization of agents, manages WebSocket connections, processes user requests, and coordinates the execution of tasks among different agents.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import os
import queue
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import logging
import re
from util import load_yaml, create_agent, parse_user_instruction, setup_logging
import copy
import json
from human_agent import HumanAgent
from datetime import datetime  # For timestamping logs and events
from pydantic import BaseModel  # For request validation
#from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process

load_dotenv()

def load_available_configs():
    """
    Function Name: load_available_configs
    Description: Loads configuration settings from environment variables that start with "CONFIG_".
                 These configurations are used to initialize agents with specific roles and tasks.
    
    Returns:
        dict: A dictionary where keys are the configuration names and values are the associated configurations.
    """
    available_configs = {}
    for key, value in os.environ.items():
        if key.startswith("CONFIG_"):
            config_name = key.replace("CONFIG_", "").lower()  # E.g., 'stock', 'post'
            available_configs[config_name] = value
    return available_configs

available_configs = load_available_configs()
app = FastAPI()

#executor = ThreadPoolExecutor()
def execute_in_process(state, step):
    """
    Function Name: execute_in_process
    Description: Executes tasks in a separate process. It is designed to handle tasks that need to be isolated from the main process.
    
    Parameters:
        state (State): The current state of the session for the user.
        step (str): The specific step or task to execute.
    """
    execute_tasks(state, step)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket interface
ws_clients = {}

# Session states per user
session_states = {}

class State:
    """
    Class Name: State
    Description: Manages the state of a user's session, including agent management, task queues, and interaction variables.
                 Each user has a separate state object to maintain their unique session data.

    Attributes:
        agents (dict): A dictionary mapping agent names to their instances for the current session.
        task_queue (asyncio.Queue): A queue to manage tasks assigned to the agents.
        user_to_agent (dict): Maps user IDs to the agents they interact with.
        started (bool): Indicates whether the session has started.
        global_channel (str): The global communication channel for the session.
        all_agents (dict): All available agents for the session.
        variables (dict): Variables loaded from the configuration file.
        interaction (dict): Interaction settings for the session.
        expected_human_agent (str): The name of the human agent expected to respond.
        human_agent_response_received (asyncio.Event): Event to signal when a response is received from a human agent.
        response_queue (asyncio.Queue): Queue to manage responses from human agents.
        config_request (bool): Flag indicating if the request originated from the CLI.
        snapshot_history (list): A list to store snapshots of the session state.
        step_request (bool): Indicates if a step selection is awaited from the user.
    """

    def __init__(self):
        self.agents = {}
        self.task_queue = asyncio.Queue()
        self.user_to_agent = {}
        self.started = False  # Each user gets their own "started" state
        self.global_channel = None
        self.all_agents = {}
        self.variables = {}
        self.interaction = {}
        self.expected_human_agent = None
        self.human_agent_response_received = asyncio.Event()
        self.response_queue = asyncio.Queue()
        self.config_request = False  # Flag to indicate if the request is from CLI
        self.snapshot_history = []  # List to store snapshot history
        self.step_request = False  # Added step_request attribute
        self.config_set = False
        self.steps= []

# Agent initialization function
def initialize_agents(state):
    """
    Function Name: initialize_agents
    Description: Initializes agents based on the configuration file specified in the environment variables.
                 This function loads agent configurations from a YAML file and sets up the required agents for the session.

    Parameters:
        state (State): The current state of the session for the user.
    """
    config_path = Path(os.getenv("CONFIG"))  # Path to YAML file
    config = load_yaml(config_path)

    # Setting variables
    state.variables = config.get('variables', {})
    state.interaction = config.get('interaction', {})

    # Creating agents
    state.all_agents = {}
    for role_name, agent_config in config['agents'].items():
        agent = create_agent(role_name, agent_config)
        state.all_agents[role_name] = agent

    # Verify that agents are correctly initialized
    for role_name, agent in state.all_agents.items():
        if agent.pre_processing_tools:
            logging.info(f"Agent: {role_name}, pre-processing tools: {[tool.__class__.__name__ for tool in agent.pre_processing_tools]}")
        if agent.post_processing_tools:
            logging.info(f"Agent: {role_name}, post-processing tools: {[tool.__class__.__name__ for tool in agent.post_processing_tools]}")
    # Reset agents
    for agent in state.all_agents.values():
        agent.reset()

# Ensure that every user has its own state
def get_or_create_user_state(user_id):
    """
    Function Name: get_or_create_user_state
    Description: Retrieves the state object for a given user ID. If no state exists, it creates one and initializes the agents.
    
    Parameters:
        user_id (str): The unique identifier for the user.
    
    Returns:
        State: The state object associated with the user.
    """
    if user_id not in session_states:
        session_states[user_id] = State()
    return session_states[user_id]

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    ws_clients[user_id] = websocket
    logging.info(f"WebSocket connection established for user: {user_id}")

    try:
        while True:
            data_task = asyncio.create_task(websocket.receive_text())
            keepalive_task = asyncio.create_task(asyncio.sleep(30))  # Keep-alive időzítő
            done, pending = await asyncio.wait(
                [data_task, keepalive_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if data_task in done:
                data = data_task.result()
                logging.info(f"Message received from {user_id}: {data}")
                await websocket.send_text(f"Message text was: {data}")
            else:
                logging.info(f"Sending keep-alive ping to user: {user_id}")
                await websocket.send_text("ping")
            
            for task in pending:
                task.cancel()

    except WebSocketDisconnect:
        logging.info(f"WebSocket connection closed for user: {user_id}")
    except Exception as e:
        logging.error(f"WebSocket connection error for user {user_id}: {e}", exc_info=True)
    finally:
        if user_id in ws_clients:
            del ws_clients[user_id]
            
# Enhanced monitoring and snapshot function
async def get_queue_items(queue):
    """
    Function Name: get_queue_items
    Description: Helper function to retrieve all items currently in an asyncio.Queue without removing them.
    
    Parameters:
        queue (asyncio.Queue): The asyncio queue from which to retrieve items.
    
    Returns:
        list: A list of items currently in the queue.
    """
    items = []
    temp_queue = asyncio.Queue()  # Temporary queue to hold items

    try:
        logging.info("Starting to retrieve items from queue...")
        while not queue.empty():
            item = await queue.get()
            logging.info(f"Item retrieved: {item}")
            items.append(item)
            await temp_queue.put(item)  # Put it into the temporary queue

        # Put all items back into the original queue
        while not temp_queue.empty():
            item = await temp_queue.get()
            await queue.put(item)
        
        logging.info(f"All items retrieved from queue: {items}")
    except Exception as e:
        logging.error(f"Error while retrieving items from queue: {e}", exc_info=True)

    return items

async def create_system_snapshot(state):
    """
    Function Name: create_system_snapshot
    Description: Captures the current state of the system, including agent states, current tasks, and interactions. 
                 The snapshot is stored in the session's history for later analysis.
    
    Parameters:
        state (State): The current state of the session for the user.
    
    Returns:
        dict: A snapshot of the current system state.
    """
    try:
        logging.info("Creating system snapshot...")

        # Retrieve current tasks from the queue
        current_tasks = await get_queue_items(state.task_queue)  # Await the async function to get queue items
        logging.info(f"Current tasks retrieved: {current_tasks}")

        # Capture the state of each agent
        agents_state = {role_name: agent.get_state() for role_name, agent in state.all_agents.items()}
        logging.info(f"Agent states captured: {agents_state}")

        # Build the snapshot dictionary
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "agents_state": agents_state,
            "current_tasks": current_tasks,
            "user_to_agent": state.user_to_agent,
            "interaction": state.interaction
        }

        # Append the snapshot to the session history
        state.snapshot_history.append(snapshot)
        logging.info(f"Snapshot created and added to history: {snapshot}")

        return snapshot

    except Exception as e:
        logging.error(f"Error while creating system snapshot: {e}", exc_info=True)
        return None

# Main task execution function (orchestration layer)
async def execute_tasks(state, step_name):
    """
    Function Name: execute_tasks
    Description: Coordinates the execution of tasks across multiple agents within a specific step of the session.
                 It manages the interaction between agents and handles retries in case of errors.
    
    Parameters:
        state (State): The current state of the session for the user.
        step_name (str): The name of the step to be executed.
    """
    from human_agent import HumanAgent
    from camel_agent import CAMELAgent

    if "steps" not in state.variables:
        logging.error("The 'steps' key is missing from the configuration.")
        await send_response(state.global_channel, "Configuration error: 'steps' key is missing.")
        state.started = False
        return

    steps = state.variables.get("steps", {})
    if len(steps) == 1:
        step_name = list(steps.keys())[0]

    flow = steps.get(step_name, None)
    if flow is None:
        logging.error(f"The step '{step_name}' is missing from the configuration.")
        await send_response(state.global_channel, f"Configuration error: step '{step_name}' is missing.")
        state.started = False
        return

    participants = flow['participants']
    state.agents['ChatManager'] = state.all_agents.get("ChatManager").clone()
    logging.info(f"ChatManager cloned with state: {state.agents['ChatManager'].get_state()}")

    for name in participants:
        if name in state.all_agents:
            state.agents[name] = state.all_agents.get(name).clone()
            logging.info(f"Cloned agent {name} with state: {state.agents[name].get_state()}")
        else:
            logging.error(f"Agent '{name}' not found in state.all_agents")

    for role_name, agent in state.agents.items():
        if agent.pre_processing_tools:
            logging.info(f"Agent: {role_name}, pre-processing tools: {[tool.__class__.__name__ for tool in agent.pre_processing_tools]}")
        if agent.post_processing_tools:
            logging.info(f"Agent: {role_name}, post-processing tools: {[tool.__class__.__name__ for tool in agent.post_processing_tools]}")

    manager_msg = copy.deepcopy(state.variables.get("inputs", {}))
    manager_msg["goal"] = flow
    inputs = manager_msg
    assistant_response = None
    chat_turn_limit = state.interaction.get("steps", 30)
    n = 0
    chat_manager = state.agents['ChatManager']

    while n < chat_turn_limit:
        n += 1
        logging.info(f"Starting chat turn {n}")
        retry = 0
        context = {"input": inputs, "previous_response": assistant_response}
        await create_system_snapshot(state)

        while retry < 4:
            try:
                manager_msg = {'role': 'user', 'content': json.dumps(context)}
                manager_output = await chat_manager.step(manager_msg)
                await send_response(state.global_channel, manager_output)

                if "CAMEL_TASK_DONE" in manager_output:
                    logging.info("Task done!")
                    state.started = False
                    break

                parsed_instruction = parse_user_instruction(manager_output)
                assistant_name = parsed_instruction["Action"]
                if assistant_name not in state.agents:
                    logging.info(f"No agent found with the name '{assistant_name}'")
                    assistant_response = f"Assistant name unknown. Context: {assistant_response}"
                    retry += 1
                    continue
                break
            except Exception as e:
                logging.error(f"Error in task execution loop: {e}", exc_info=True)
                retry += 1
                await asyncio.sleep(1)

        if not state.started:
            break

        assistant_agent = state.agents[assistant_name]
        assistant_msg = {
            'role': 'user',
            'content': f"Instruction: {parsed_instruction['Question']}\nThought: {parsed_instruction['Thought']}\nAction Input: {parsed_instruction['Action Input']}\nInput: {inputs}\nPrevious response: {assistant_response}"
        }

        logging.info(f"AI user (ChatManager): {assistant_msg}")
        if isinstance(assistant_agent, HumanAgent):
            state.expected_human_agent = assistant_name
            await state.task_queue.put(parsed_instruction['Action Input'])
            logging.info("Chatmanager put question to task_queue!")
            await send_task_to_human_agent(state, assistant_name, parsed_instruction['Action Input'])
            response = await wait_for_human_response(state, assistant_name)
            if response is None:
                logging.error(f"No response received from {assistant_name}")
                break
            assistant_msg['content'] += f"\nHuman response: {response}"
            state.expected_human_agent = None


        # Assistant step
        logging.info(f"Preparing to send the following message to {assistant_name}: {assistant_msg}")

        for i in range(3):
            try:
                # Handle both async and sync step methods
                if asyncio.iscoroutinefunction(assistant_agent.step):
                    assistant_response = await assistant_agent.step(assistant_msg)
                else:
                    assistant_response = assistant_agent.step(assistant_msg)
                logging.info(f"AI Assistant ({assistant_agent.name}): {assistant_response}")
                break
            except Exception as e:
                logging.warning(f"Error in assistant step: {e}", exc_info=True)
                assistant_msg['content'] = f"Retry {i} because of error: {e} \n" + assistant_msg['content']
                continue
        else:
            logging.error(f"Error in assistant step", exc_info=True)
            assistant_response = "Solution: No solution as there was an error in assistant step"

        await send_response(state.global_channel, assistant_response)
        inputs["previous_response"] = assistant_response

    logging.info(f"Finished chat turn {n}")
    if not state.started:
        final = await chat_manager.step({'role': 'user', 'content': """Provide your Final Answer based on your system prompt."""})
        with open('./post.md', "w") as file:
            print(final, file=file)
        await send_response(state.global_channel, final)

    for key, agent in state.agents.items():
        await agent.end()

async def wait_for_human_response(state, assistant_name):
    """
    Function Name: wait_for_human_response
    Description: Waits for a response from a human agent with a specified timeout.
    
    Parameters:
        state (State): The current state of the session for the user.
        assistant_name (str): The name of the human agent expected to respond.
    
    Returns:
        str: The response received from the human agent, or None if a timeout occurs.
    """
    logging.info(f"Waiting for response from {assistant_name}")
    state.human_agent_response_received.clear()  # Clear the event
    try:
        await asyncio.wait_for(state.human_agent_response_received.wait(), timeout=60.0)  # Set a timeout of 60 seconds
    except asyncio.TimeoutError:
        logging.error(f"Timeout waiting for response from {assistant_name}")
        return None

    # Get the response message from the queue
    response = await state.response_queue.get()
    logging.info(f"Received response from queue: {response}")

    # Naplózás az ügynök nevével és a válasszal
    logging.info(f"Passing response to assistant: {assistant_name}")
    return response

async def send_task_to_human_agent(state, assistant_name, msg):
    """
    Function Name: send_task_to_human_agent
    Description: Sends a task to the appropriate human agent via WebSocket.
    
    Parameters:
        state (State): The current state of the session for the user.
        assistant_name (str): The name of the human agent to whom the task is assigned.
        msg (str): The message or task details to be sent to the human agent.
    """
    # Send the task to the appropriate WebSocket client
    for user_id, agent_name in state.user_to_agent.items():
        if agent_name == assistant_name:
            websocket = ws_clients.get(user_id)
            if websocket:
                await websocket.send_text(f"Task assigned to {assistant_name}: {msg}")
                logging.info(f"Task sent to {assistant_name}: {msg}")
                return
            else:
                logging.error(f"No WebSocket connection found for {assistant_name} (user_id: {user_id})")

# Send response through WebSocket
async def send_response(channel: str, message: str):
    """
    Function Name: send_response
    Description: Sends a formatted response message through WebSocket to the specified channel.
    
    Parameters:
        channel (str): The channel or user ID to which the response should be sent.
        message (str): The message content to be sent.
    """
    formatted_message = format_message(message)
    logging.info(f"Sending response to channel {channel}: {formatted_message}")

    # Send message to the appropriate WebSocket client
    websocket = ws_clients.get(channel)
    if websocket:
        tasks = []
        tasks.append(asyncio.create_task(websocket.send_text(formatted_message)))
        await asyncio.gather(*tasks)
    else:
        logging.warning(f"No WebSocket connection found for channel: {channel}")

def format_message(message: str) -> str:
    """
    Function Name: format_message
    Description: Formats a message by converting it to JSON if necessary. This function ensures that the message is properly structured before sending it.
    
    Parameters:
        message (str): The message content to be formatted.
    
    Returns:
        str: The formatted message.
    """
    try:
        if isinstance(message, dict):
            return json.dumps(message)
        data = json.loads(message)
        if 'role' in data and 'content' in data:
            return data['content']
        return message
    except json.JSONDecodeError:
        return str(message)

# Model for CLI events
class CLIRequest(BaseModel):
    """
    Class Name: CLIRequest
    Description: Data model for handling CLI event requests. This class is used to validate incoming requests to the /cli/events endpoint.

    Attributes:
        user_id (str): The unique identifier of the user making the request.
        text (str): The text or command sent by the user via CLI.
    """
    user_id: str
    text: str

@app.post("/cli/events")
async def cli_events(request: CLIRequest):
    """
    Function Name: cli_events
    Description: Handles CLI events by processing the user's text input and executing the corresponding actions.
                 It manages the state of the session and triggers agent initialization or task execution as needed.
    
    Parameters:
        request (CLIRequest): The request object containing the user ID and text input.
    
    Returns:
        JSONResponse: A response indicating the outcome of the CLI event processing.
    """
    user_id = request.user_id
    message = request.text.strip().lower()

    state = session_states.get(user_id)
    if state and state.expected_human_agent:
        logging.info(f"Received human response: {message}")
        await state.response_queue.put(message)  # Insert the response into the queue
        state.human_agent_response_received.set()  # Set the event
        state.expected_human_agent = None  # Reset after handling the human response
        return JSONResponse({"message": "Human agent response received."}, status_code=200)

    if message == "start" and not state:
        config_options = list(available_configs.keys())
        options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(config_options)])
        await send_response(user_id, f"Please choose a configuration by typing the corresponding number:\n{options_text}")
        get_or_create_user_state(user_id)
        session_states[user_id].config_request = True
        session_states[user_id].global_channel = user_id  # Set the global_channel
        return JSONResponse({"message": "Configuration choice requested."}, status_code=200)
    """
    Client-side state management: This branch is executed when state.config_request is true, indicating that the user is in the process of choosing a configuration.
    Configuration selection: The user must provide a number corresponding to an item in the list of configurations.
    Step selection: If only one step is available in the configuration, it is automatically selected. If there are multiple steps, the user is prompted to choose one.
    Background process initiation: Once a step is chosen, a background process (execute_tasks) is initiated to execute the step.
    """
    if state and state.config_request:
        try:
            choice_index = int(message) - 1
            if 0 <= choice_index < len(available_configs):
                chosen_config_key = list(available_configs.keys())[choice_index]
                chosen_config_path = available_configs[chosen_config_key]
                os.environ["CONFIG"] = chosen_config_path
                state.config_request = False
                state.config_set = True
                initialize_agents(state)
                
                # Step selection
                state.steps = state.variables.get("steps", [])
                if len(state.steps) == 1:
                    step = list(state.steps.keys())[0]  # If only one item, select automatically
                else:
                    step_options = list(state.steps.keys())
                    options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(step_options)])
                    await send_response(user_id, f"Please choose a step to start by typing the corresponding number:\n{options_text}")
                    session_states[user_id].steps = step_options
                    session_states[user_id].step_request = True
                    session_states[user_id].global_channel = user_id  # Set the global_channel
                    return JSONResponse({"message": "Configuration choice requested."}, status_code=200)



                # Execute the step
                session_states[user_id].global_channel = user_id  # Set the global_channel
                if not state.started:
                    session_states[user_id].started = True
                    # Run the task in a separate thread
                    #loop = asyncio.get_running_loop()
                    #await loop.run_in_executor(executor, execute_tasks, state, step)
                    # asyncio only
                    asyncio.create_task(execute_tasks(state, step))
                    # Run in a separate process
                    #process = Process(target=execute_in_process, args=(state, step))
                    #process.start()

                    return JSONResponse({"message": f"Process for '{chosen_config_key}' and step '{step}' started."}, status_code=200)
                else:
                    return JSONResponse({"message": "Process already running."}, status_code=400)
            else:
                await send_response(user_id, "Invalid choice. Please try again.")
        except ValueError:
            await send_response(user_id, "Invalid input. Please enter a number corresponding to the configuration.")
        return JSONResponse({"message": "Configuration choice processed."}, status_code=200)

    """
    Step selection: This branch is executed when state.step_request is true, indicating that the user is selecting a step based on the chosen configuration.
    Step validation: Checks if the step selected by the user exists in the steps list.
    Background process initiation: If the selected step is valid, a background process (execute_tasks) is initiated to execute the step.
    """
    if state and state.step_request:
        choice_index = int(message) - 1
        available_steps = state.steps
        if 0 <= choice_index < len(available_steps):
            step = available_steps[choice_index]
            state.step_request = False  # Step selection complete
            state.global_channel = user_id  # Set the global_channel before starting the step
            if not state.started:
                state.started = True
                # Run the task in a separate thread
                #loop = asyncio.get_running_loop()
                #await loop.run_in_executor(executor, execute_tasks, state, step)
                # asyncio only
                asyncio.create_task(execute_tasks(state, step))
                # Separate process
                #process = Process(target=execute_in_process, args=(state, step))
                #process.start()
                return JSONResponse({"message": f"Step '{step}' started."}, status_code=200)
            else:
                return JSONResponse({"message": "Process already running."}, status_code=400)
        else:
            await send_response(user_id, "Invalid step choice. Please try again.")
            return JSONResponse({"message": "Invalid step choice."}, status_code=400)

    if not state or not state.config_set:
        await send_response(user_id, "Please start by typing 'start' and choosing a configuration.")
        return JSONResponse({"message": "Start not initiated properly."}, status_code=400)

    await send_response(user_id, f"Received message: {message}")
    return JSONResponse({"message": "Message processed."}, status_code=200)

if __name__ == "__main__":
    setup_logging()
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8081)
    except Exception as e:
        logging.error(f"Error in main execution: {e}", exc_info=True)

