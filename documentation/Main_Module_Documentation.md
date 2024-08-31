## Module Overview

### File Name: `main.py`

This file serves as the orchestration layer for a multi-agent AI solution. It handles the initialization of agents, manages WebSocket connections, processes user requests, and coordinates the execution of tasks among different agents.

### Author: 
- Sandor Seres (sseres@code.hu)

### Date: 
- 2024-08-31

### Version: 
- 1.0

### License: 
- Creative Commons Zero v1.0 Universal

## Function Descriptions

### `load_available_configs()`
Loads configuration settings from environment variables that start with "CONFIG_". These configurations are used to initialize agents with specific roles and tasks.

#### Returns:
- **dict**: A dictionary where keys are the configuration names and values are the associated configurations.

### `execute_in_process(state, step)`
Executes tasks in a separate process. It is designed to handle tasks that need to be isolated from the main process.

#### Parameters:
- **state (State)**: The current state of the session for the user.
- **step (str)**: The specific step or task to execute.

### `initialize_agents(state)`
Initializes agents based on the configuration file specified in the environment variables. This function loads agent configurations from a YAML file and sets up the required agents for the session.

#### Parameters:
- **state (State)**: The current state of the session for the user.

### `get_or_create_user_state(user_id)`
Retrieves the state object for a given user ID. If no state exists, it creates one and initializes the agents.

#### Parameters:
- **user_id (str)**: The unique identifier for the user.

#### Returns:
- **State**: The state object associated with the user.

### `websocket_endpoint(websocket: WebSocket, user_id: str)`
Handles WebSocket connections for users. It listens for messages and sends keep-alive pings.

#### Parameters:
- **websocket (WebSocket)**: The WebSocket connection instance.
- **user_id (str)**: The unique identifier for the user.

### `get_queue_items(queue)`
Helper function to retrieve all items currently in an asyncio.Queue without removing them.

#### Parameters:
- **queue (asyncio.Queue)**: The asyncio queue from which to retrieve items.

#### Returns:
- **list**: A list of items currently in the queue.

### `create_system_snapshot(state)`
Captures the current state of the system, including agent states, current tasks, and interactions. The snapshot is stored in the session's history for later analysis.

#### Parameters:
- **state (State)**: The current state of the session for the user.

#### Returns:
- **dict**: A snapshot of the current system state.

### `execute_tasks(state, step_name)`
Coordinates the execution of tasks across multiple agents within a specific step of the session. It manages the interaction between agents and handles retries in case of errors.

#### Parameters:
- **state (State)**: The current state of the session for the user.
- **step_name (str)**: The name of the step to be executed.

### `wait_for_human_response(state, assistant_name)`
Waits for a response from a human agent with a specified timeout.

#### Parameters:
- **state (State)**: The current state of the session for the user.
- **assistant_name (str)**: The name of the human agent expected to respond.

#### Returns:
- **str**: The response received from the human agent, or None if a timeout occurs.

### `send_task_to_human_agent(state, assistant_name, msg)`
Sends a task to the appropriate human agent via WebSocket.

#### Parameters:
- **state (State)**: The current state of the session for the user.
- **assistant_name (str)**: The name of the human agent to whom the task is assigned.
- **msg (str)**: The message or task details to be sent to the human agent.

### `send_response(channel: str, message: str)`
Sends a formatted response message through WebSocket to the specified channel.

#### Parameters:
- **channel (str)**: The channel or user ID to which the response should be sent.
- **message (str)**: The message content to be sent.

### `format_message(message: str) -> str`
Formats a message by converting it to JSON if necessary. This function ensures that the message is properly structured before sending it.

#### Parameters:
- **message (str)**: The message content to be formatted.

#### Returns:
- **str**: The formatted message.

### `cli_events(request: CLIRequest)`
Handles CLI events by processing the user's text input and executing the corresponding actions. It manages the state of the session and triggers agent initialization or task execution as needed.

#### Parameters:
- **request (CLIRequest)**: The request object containing the user ID and text input.

#### Returns:
- **JSONResponse**: A response indicating the outcome of the CLI event processing.

## Class Descriptions

### `State`
Manages the state of a user's session, including agent management, task queues, and interaction variables. Each user has a separate state object to maintain their unique session data.

#### Attributes:
- **agents (dict)**: A dictionary mapping agent names to their instances for the current session.
- **task_queue (asyncio.Queue)**: A queue to manage tasks assigned to the agents.
- **user_to_agent (dict)**: Maps user IDs to the agents they interact with.
- **started (bool)**: Indicates whether the session has started.
- **global_channel (str)**: The global communication channel for the session.
- **all_agents (dict)**: All available agents for the session.
- **variables (dict)**: Variables loaded from the configuration file.
- **interaction (dict)**: Interaction settings for the session.
- **expected_human_agent (str)**: The name of the human agent expected to respond.
- **human_agent_response_received (asyncio.Event)**: Event to signal when a response is received from a human agent.
- **response_queue (asyncio.Queue)**: Queue to manage responses from human agents.
- **cli_request (bool)**: Flag indicating if the request originated from the CLI.
- **snapshot_history (list)**: A list to store snapshots of the session state.
- **step_request (bool)**: Indicates if a step selection is awaited from the user.

## Detailed Algorithm Explanations

### Initialization and Configuration
1. **Loading Configurations**: The `load_available_configs` function loads configurations from environment variables, allowing dynamic agent initialization based on user input.
2. **Agent Initialization**: The `initialize_agents` function sets up agents based on the loaded configurations, ensuring that each user session has the necessary agents available.

### WebSocket Management
- The `websocket_endpoint` function manages WebSocket connections, allowing real-time communication between the server and clients. It handles incoming messages and sends keep-alive pings to maintain the connection.

### Task Execution
- The `execute_tasks` function orchestrates the execution of tasks across multiple agents, managing the flow of information and ensuring that agents can communicate effectively. It handles retries and logs actions for debugging.

### State Management
- The `State` class encapsulates all relevant information for a user's session, including agents, task queues, and interaction settings. This allows for easy management of user-specific data.

## Basic Examples

### Loading Configurations
```python
available_configs = load_available_configs()
```

### Initializing Agents
```python
state = State()
initialize_agents(state)
```

### WebSocket Connection
```python
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    # Handle messages...
```

### Sending a Response
```python
await send_response(user_id, "Your task has been processed.")
```

### Executing Tasks
```python
asyncio.create_task(execute_tasks(state, step_name))
```

## Expected Outputs
- Loading configurations will return a dictionary of available configurations.
- Initializing agents will set up the agents based on the loaded configurations.
- Sending a response will deliver a message to the specified user via WebSocket.
- Executing tasks will coordinate actions among agents and manage user interactions.

This documentation provides a comprehensive overview of the `main.py` module, its functions, classes, and their usage within a multi-agent AI system context.
