## Overview

The `main.py` file serves as the orchestration layer for a multi-agent AI solution. It handles the initialization of agents, manages WebSocket connections, processes user requests, and coordinates the execution of tasks among different agents.

### Author
- Sandor Seres (sseres@code.hu)

### Date
- 2024-08-31

### Version
- 1.0

### License
- Creative Commons Zero v1.0 Universal

## Functions and Classes

### Function: load_available_configs()
Loads configuration settings from environment variables that start with "CONFIG_". These configurations are used to initialize agents with specific roles and tasks.

**Returns:**
- `dict`: A dictionary where keys are the configuration names and values are the associated configurations.

### Function: execute_in_process(state, step)
Executes tasks in a separate process. It is designed to handle tasks that need to be isolated from the main process.

**Parameters:**
- `state (State)`: The current state of the session for the user.
- `step (str)`: The specific step or task to execute.

### Class: State
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

### Function: initialize_agents(state)
Initializes agents based on the configuration file specified in the environment variables.

**Parameters:**
- `state (State)`: The current state of the session for the user.

### Function: get_or_create_user_state(user_id)
Retrieves the state object for a given user ID. If no state exists, it creates one and initializes the agents.

**Parameters:**
- `user_id (str)`: The unique identifier for the user.

**Returns:**
- `State`: The state object associated with the user.

### WebSocket Interface
Handles WebSocket connections for real-time communication between the server and clients.

#### Function: websocket_endpoint(websocket: WebSocket, user_id: str)
Manages the connection lifecycle, including accepting messages, sending responses, and handling disconnections.

**Parameters:**
- `websocket (WebSocket)`: The WebSocket connection object.
- `user_id (str)`: The unique identifier for the user associated with this WebSocket connection.

### Function: get_queue_items(queue)
Helper function to retrieve all items currently in an asyncio.Queue without removing them.

**Parameters:**
- `queue (asyncio.Queue)`: The asyncio queue from which to retrieve items.

**Returns:**
- `list`: A list of items currently in the queue.

### Function: create_system_snapshot(state)
Captures the current state of the system, including agent states, current tasks, and interactions.

**Parameters:**
- `state (State)`: The current state of the session for the user.

**Returns:**
- `dict`: A snapshot of the current system state.

### Function: execute_tasks(state, step_name)
Coordinates the execution of tasks across multiple agents within a specific step of the session.

**Parameters:**
- `state (State)`: The current state of the session for the user.
- `step_name (str)`: The name of the step to be executed.

### Function: wait_for_human_response(state, assistant_name)
Waits for a response from a human agent with a specified timeout.

**Parameters:**
- `state (State)`: The current state of the session for the user.
- `assistant_name (str)`: The name of the human agent expected to respond.

**Returns:**
- `str`: The response received from the human agent, or None if a timeout occurs.

### Function: send_task_to_human_agent(state, assistant_name, msg)
Sends a task to the appropriate human agent via WebSocket.

**Parameters:**
- `state (State)`: The current state of the session for the user.
- `assistant_name (str)`: The name of the human agent to whom the task is assigned.
- `msg (str)`: The message or task details to be sent to the human agent.

### Function: send_response(channel: str, message: str)
Sends a formatted response message through WebSocket to the specified channel.

**Parameters:**
- `channel (str)`: The channel or user ID to which the response should be sent.
- `message (str)`: The message content to be sent.

### Function: format_message(message: str) -> str
Formats a message by converting it to JSON if necessary.

**Parameters:**
- `message (str)`: The message content to be formatted.

**Returns:**
- `str`: The formatted message.

### Class: CLIRequest
Data model for handling CLI event requests. This class is used to validate incoming requests to the /cli/events endpoint.

#### Attributes:
- **user_id (str)**: The unique identifier of the user making the request.
- **text (str)**: The text or command sent by the user via CLI.

### Function: cli_events(request: CLIRequest)
Handles CLI events by processing the user's text input and executing the corresponding actions.

**Parameters:**
- `request (CLIRequest)`: The request object containing the user ID and text input.

**Returns:**
- `JSONResponse`: A response indicating the outcome of the CLI event processing.

## Examples

### Basic Usage

```python
# Start the FastAPI application
if __name__ == "__main__":
    setup_logging()
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8081)
    except Exception as e:
        logging.error(f"Error in main execution: {e}", exc_info=True)
```

## Conclusion

The `main.py` file serves as the central hub for managing interactions between multiple agents in a multi-agent AI system. It facilitates real-time communication, task orchestration, and user session management, making it a critical component of the overall architecture.
