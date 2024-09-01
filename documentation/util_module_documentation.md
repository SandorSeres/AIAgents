Utility Module Documentation

## File: util.py

### Description
This file contains various utility functions and classes used in an AI-based application. These include logging setup, YAML configuration loading, agent creation, cost calculation, and markdown conversion to Facebook format. The utilities support core operations, enabling effective management of agents and their interactions within the system.

### Functions

#### `setup_logging()`
Sets up the logging configuration for the application. Logs are written to both the console and a file named 'app.log'. The logging format includes timestamps, log level, logger name, message, and source file with line number.

#### `load_yaml(file_path)`
Loads and parses a YAML configuration file, replacing environment variables.

- **Parameters**:
  - `file_path (str)`: The path to the YAML file.

- **Returns**:
  - `dict`: The parsed YAML file as a dictionary with environment variables substituted.

- **Logs**:
  - Info: On successful loading of the YAML file.
  - Error: If there is an issue loading or parsing the YAML file.

#### `create_agent(role_name, agent_config)`
Creates an agent based on the provided configuration. Supports `HumanAgent` and `CAMELAgent` types.

- **Parameters**:
  - `role_name (str)`: The name of the role for the agent.
  - `agent_config (dict)`: Configuration details for the agent, including its type and associated tools.

- **Returns**:
  - Object: An instance of the created agent.

- **Logs**:
  - Info: On successful creation of the agent.
  - Error: If there is an issue during the creation of the agent.

#### `extract_json_string(text)`
Extracts a JSON string from a block of text.

- **Parameters**:
  - `text (str)`: The text containing the JSON string.

- **Returns**:
  - `str`: The extracted JSON string, or an empty JSON object if extraction fails.

- **Logs**:
  - Warning: If there is an error during JSON extraction.

#### `parse_user_instruction(instruction)`
Parses a user instruction, extracting and returning the JSON content.

- **Parameters**:
  - `instruction (str)`: The instruction text containing JSON data.

- **Returns**:
  - `dict`: The parsed JSON data.

- **Logs**:
  - Info: On successful parsing of the user instruction.
  - Warning: If there is an error during JSON parsing.

#### `calculate_costs(usage_metrics, model_input_price, model_output_price, unit_of_tokens)`
Calculates and logs the cost of an AI model's usage based on token consumption.

- **Parameters**:
  - `usage_metrics (object)`: The usage metrics object containing token counts.
  - `model_input_price (float)`: The cost per unit of input tokens.
  - `model_output_price (float)`: The cost per unit of output tokens.
  - `unit_of_tokens (int)`: The number of tokens per unit for pricing.

- **Logs**:
  - Info: When costs are successfully calculated and saved.
  - Error: If there is an issue during cost calculation.

#### `markdown_to_facebook(text)`
Converts markdown text to a format suitable for posting on Facebook, handling various HTML elements and formatting.

- **Parameters**:
  - `text (str)`: The markdown text to be converted.

- **Returns**:
  - `str`: The text converted to Facebook format.

- **Logs**:
  - Info: When the conversion is successful.
  - Error: If there is an issue during the conversion process.

### Detailed Algorithm Explanations

1. **Logging Setup**:
   - The `setup_logging` function configures logging to capture application events and errors.

2. **YAML Loading**:
   - The `load_yaml` function reads a YAML file and substitutes environment variables, returning a configuration dictionary.

3. **Agent Creation**:
   - The `create_agent` function instantiates agents based on their configuration, initializing necessary tools.

4. **JSON Extraction**:
   - The `extract_json_string` function retrieves JSON strings from text, handling potential errors gracefully.

5. **User Instruction Parsing**:
   - The `parse_user_instruction` function extracts and parses JSON data from user instructions.

6. **Cost Calculation**:
   - The `calculate_costs` function computes costs based on token usage and logs the results.

7. **Markdown Conversion**:
   - The `markdown_to_facebook` function converts markdown text to a format suitable for Facebook, ensuring proper formatting.

### Basic Examples

#### Example of Setting Up Logging
```python
setup_logging()
```

#### Example of Loading a YAML Configuration
```python
config = load_yaml("config.yaml")
```

#### Example of Creating an Agent
```python
agent_config = {
    'type': 'HumanAgent',
    'role_name': 'User',
    'role_description': 'A human user in the system.',
    'tools': {
        'pre-processing': [],
        'post-processing': []
    }
}
agent = create_agent("User", agent_config)
```

#### Example of Extracting JSON String
```python
json_string = extract_json_string("Here is some text with JSON: {\"key\": \"value\"}")
```

#### Example of Parsing User Instruction
```python
instruction = '{"Action": "do_something", "Data": {"key": "value"}}'
parsed_data = parse_user_instruction(instruction)
```

#### Example of Calculating Costs
```python
usage_metrics = {'prompt_tokens': 100, 'completion_tokens': 50}
calculate_costs(usage_metrics, model_input_price=0.01, model_output_price=0.02, unit_of_tokens=1000)
```

#### Example of Converting Markdown to Facebook Format
```python
facebook_text = markdown_to_facebook("## Hello World\nThis is a **test**.")
```

### Expected Outputs
- The `setup_logging` function configures logging for the application.
- The `load_yaml` function returns a dictionary of configuration settings.
- The `create_agent` function returns an instance of the specified agent.
- The `extract_json_string` function returns the extracted JSON string.
- The `parse_user_instruction` function returns the parsed JSON data.
- The `calculate_costs` function logs the calculated costs.
- The `markdown_to_facebook` function returns the formatted text suitable for Facebook.

