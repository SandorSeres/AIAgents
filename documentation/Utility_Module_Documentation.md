Utility Module Documentation

## Module Overview

### File Name: `util.py`

This file contains various utility functions and classes used in an AI-based application. These include logging setup, YAML configuration loading, agent creation, cost calculation, and markdown conversion to Facebook format. The utilities support core operations, enabling effective management of agents and their interactions within the system.

### Author: 
- Sandor Seres (sseres@code.hu)

### Date: 
- 2024-08-31

### Version: 
- 1.0

### License: 
- Creative Commons Zero v1.0 Universal

## Function Descriptions

### `setup_logging()`
Sets up the logging configuration for the application. Logs are written to both the console and a file named 'app.log'. The logging format includes timestamps, log level, logger name, message, and source file with line number.

### `load_yaml(file_path)`
Loads and parses a YAML configuration file, replacing environment variables.

#### Parameters:
- **file_path (str)**: The path to the YAML file.

#### Returns:
- **dict**: The parsed YAML file as a dictionary with environment variables substituted.

#### Logs:
- **Info**: On successful loading of the YAML file.
- **Error**: If there is an issue loading or parsing the YAML file.

### `create_agent(role_name, agent_config)`
Creates an agent based on the provided configuration. Supports `HumanAgent` and `CAMELAgent` types.

#### Parameters:
- **role_name (str)**: The name of the role for the agent.
- **agent_config (dict)**: Configuration details for the agent, including its type and associated tools.

#### Returns:
- **Object**: An instance of the created agent.

#### Logs:
- **Info**: On successful creation of the agent.
- **Error**: If there is an issue during the creation of the agent.

### `extract_json_string(text)`
Extracts a JSON string from a block of text.

#### Parameters:
- **text (str)**: The text containing the JSON string.

#### Returns:
- **str**: The extracted JSON string, or an empty JSON object if extraction fails.

#### Logs:
- **Warning**: If there is an error during JSON extraction.

### `parse_user_instruction(instruction)`
Parses a user instruction, extracting and returning the JSON content.

#### Parameters:
- **instruction (str)**: The instruction text containing JSON data.

#### Returns:
- **dict**: The parsed JSON data.

#### Logs:
- **Info**: On successful parsing of the user instruction.
- **Warning**: If there is an error during JSON parsing.

### `calculate_costs(usage_metrics, model_input_price, model_output_price, unit_of_tokens)`
Calculates and logs the cost of an AI model's usage based on token consumption.

#### Parameters:
- **usage_metrics (object)**: The usage metrics object containing token counts.
- **model_input_price (float)**: The cost per unit of input tokens.
- **model_output_price (float)**: The cost per unit of output tokens.
- **unit_of_tokens (int)**: The number of tokens per unit for pricing.

#### Logs:
- **Info**: When costs are successfully calculated and saved.
- **Error**: If there is an issue during cost calculation.

### `markdown_to_facebook(text)`
Converts markdown text to a format suitable for posting on Facebook, handling various HTML elements and formatting.

#### Parameters:
- **text (str)**: The markdown text to be converted.

#### Returns:
- **str**: The text converted to Facebook format.

#### Logs:
- **Info**: When the conversion is successful.
- **Error**: If there is an issue during the conversion process.

## Detailed Algorithm Explanations

### Logging Setup
- The `setup_logging` function configures the logging system to output logs to both the console and a file, ensuring that all relevant information is captured for debugging and monitoring.

### YAML Configuration Loading
1. **Loading YAML**: The `load_yaml` function reads a YAML file, replaces any environment variables, and returns the configuration as a dictionary. It handles errors gracefully, logging any issues encountered during the process.

### Agent Creation
1. **Creating Agents**: The `create_agent` function instantiates agents based on the provided configuration. It supports different agent types and initializes any specified tools, logging the process for transparency.

### JSON Extraction and Parsing
1. **Extracting JSON**: The `extract_json_string` function retrieves a JSON string from a larger text block, while `parse_user_instruction` processes user instructions to extract and return the relevant JSON data.

### Cost Calculation
1. **Calculating Costs**: The `calculate_costs` function computes the costs associated with AI model usage based on token consumption and logs the results for record-keeping.

### Markdown Conversion
1. **Markdown to Facebook**: The `markdown_to_facebook` function converts markdown text into a format suitable for Facebook, ensuring that the content is appropriately formatted for social media sharing.

## Basic Examples

### Setting Up Logging
```python
setup_logging()
```

### Loading a YAML Configuration
```python
config = load_yaml("config.yaml")
```

### Creating an Agent
```python
agent_config = {
    "type": "HumanAgent",
    "role_name": "Alice",
    "role_description": "A human agent."
}
agent = create_agent("Alice", agent_config)
```

### Extracting JSON from Text
```python
json_string = extract_json_string("Here is some text with JSON: {\"key\": \"value\"}")
```

### Parsing User Instructions
```python
instruction = '{"Action": "do_something", "Parameters": {"key": "value"}}'
parsed_instruction = parse_user_instruction(instruction)
```

### Calculating Costs
```python
calculate_costs(usage_metrics, 0.01, 0.02, 1000)
```

### Converting Markdown to Facebook Format
```python
facebook_text = markdown_to_facebook("## Hello World\nThis is a **test**.")
```

## Expected Outputs
- Setting up logging will initialize the logging system.
- Loading a YAML configuration will return a dictionary of settings.
- Creating an agent will return an instance of the specified agent type.
- Extracting JSON will yield the relevant JSON string or an empty object.
- Parsing user instructions will return a dictionary of parsed data.
- Calculating costs will log the calculated costs and save them to a file.
- Converting markdown will return the formatted text suitable for Facebook.

This documentation provides a comprehensive overview of the `util.py` module, its functions, and their usage within an AI-based application context.

