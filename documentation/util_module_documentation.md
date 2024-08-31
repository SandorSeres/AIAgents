Utility Module Documentation

## Overview

The `util.py` file contains various utility functions and classes used in an AI-based application. These include logging setup, YAML configuration loading, agent creation, cost calculation, and markdown conversion to Facebook format. The utilities support core operations, enabling effective management of agents and their interactions within the system.

### Author
- Sandor Seres (sseres@code.hu)

### Date
- 2024-08-31

### Version
- 1.0

### License
- Creative Commons Zero v1.0 Universal

## Functions and Classes

### Function: setup_logging()
Sets up the logging configuration for the application. Logs are written to both the console and a file named 'app.log'.

### Function: load_yaml(file_path)
Loads and parses a YAML configuration file, replacing environment variables.

**Parameters:**
- `file_path (str)`: The path to the YAML file.

**Returns:**
- `dict`: The parsed YAML file as a dictionary with environment variables substituted.

**Logs:**
- Info: On successful loading of the YAML file.
- Error: If there is an issue loading or parsing the YAML file.

### Function: create_agent(role_name, agent_config)
Creates an agent based on the provided configuration. Supports `HumanAgent` and `CAMELAgent` types.

**Parameters:**
- `role_name (str)`: The name of the role for the agent.
- `agent_config (dict)`: Configuration details for the agent, including its type and associated tools.

**Returns:**
- `Object`: An instance of the created agent.

**Logs:**
- Info: On successful creation of the agent.
- Error: If there is an issue during the creation of the agent.

### Function: extract_json_string(text)
Extracts a JSON string from a block of text.

**Parameters:**
- `text (str)`: The text containing the JSON string.

**Returns:**
- `str`: The extracted JSON string, or an empty JSON object if extraction fails.

**Logs:**
- Warning: If there is an error during JSON extraction.

### Function: parse_user_instruction(instruction)
Parses a user instruction, extracting and returning the JSON content.

**Parameters:**
- `instruction (str)`: The instruction text containing JSON data.

**Returns:**
- `dict`: The parsed JSON data.

**Logs:**
- Info: On successful parsing of the user instruction.
- Warning: If there is an error during JSON parsing.

### Function: calculate_costs(usage_metrics, model_input_price, model_output_price, unit_of_tokens)
Calculates and logs the cost of an AI model's usage based on token consumption.

**Parameters:**
- `usage_metrics (object)`: The usage metrics object containing token counts.
- `model_input_price (float)`: The cost per unit of input tokens.
- `model_output_price (float)`: The cost per unit of output tokens.
- `unit_of_tokens (int)`: The number of tokens per unit for pricing.

**Logs:**
- Info: When costs are successfully calculated and saved.
- Error: If there is an issue during cost calculation.

### Function: markdown_to_facebook(text)
Converts markdown text to a format suitable for posting on Facebook, handling various HTML elements and formatting.

**Parameters:**
- `text (str)`: The markdown text to be converted.

**Returns:**
- `str`: The text converted to Facebook format.

**Logs:**
- Info: When the conversion is successful.
- Error: If there is an issue during the conversion process.

## Examples

### Basic Usage

```python
# Setup logging
setup_logging()

# Load YAML configuration
config = load_yaml("config.yaml")

# Create an agent
agent_config = {
    'type': 'HumanAgent',
    'role_name': 'User',
    'role_description': 'A simulated human agent.'
}
agent = create_agent('User', agent_config)

# Calculate costs
usage_metrics = ...  # Assume this is defined elsewhere
calculate_costs(usage_metrics, model_input_price=0.01, model_output_price=0.02, unit_of_tokens=1000)

# Convert markdown to Facebook format
facebook_text = markdown_to_facebook("## Hello World\nThis is a **test**.")
print(facebook_text)
```

## Conclusion

The `util.py` file provides essential utility functions that facilitate various operations within the AI application, including logging, configuration management, agent creation, cost calculation, and content formatting for social media. These utilities enhance the overall functionality and maintainability of the system.
