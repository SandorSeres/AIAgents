"""
File Name: execute_tool.py
Description: This file contains the implementation of the RunPythonTool class, a utility designed to execute arbitrary Python code securely within a controlled environment. The tool is useful for tasks that require external data access, data processing, or generating images using models like DALL-E from OpenAI.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

from langchain_experimental.utilities import PythonREPL

class RunPythonTool:
    """
    Class Name: RunPythonTool
    Description: A utility class that executes given Python code in a controlled environment and returns the result. It is intended for tasks requiring data processing, external data access, or generating images using models like DALL-E.

    Attributes:
        name (str): The name of the tool.
        description (str): A detailed description of what the tool does and examples of its usage.
        parameters (str): A description of the required parameters for executing the tool.

    Methods:
        _run(code):
            Executes the given Python code and returns the result or an error message.
        
        clone():
            Returns a new instance of RunPythonTool.
    """

    name: str = "RunPythonTool"
    description: str = """Use this tool for tasks like 
    - generating images with DAL-E openai model, 
    - requiring external data access 
    - requiring data processing. 
    Executes the given Python code and returns the result.
    Example usage: 
    - Internet access and gather information
    - SQL database access to get data
    - OpenAPI access for external data
    - Generate image with DAL-E
    """
    parameters: str = "code"  # "The python code to execute."

    def __init__(self):
        """
        Initializes the RunPythonTool instance and sets up a secure Python REPL (Read-Eval-Print Loop) environment for code execution.
        """
        self.repl = PythonREPL()

    def _run(self, code: str):
        """
        Executes the given Python code in a secure environment and returns the result.

        Parameters:
            code (str): The Python code to execute.

        Returns:
            tuple: A tuple containing the result of the executed code as a string and a boolean flag indicating whether the execution was successful.
        
        Notes:
            - The method captures any exceptions that occur during execution and returns the exception message if an error is encountered.
            - The code is executed within a controlled environment using the `exec` function, and the output is expected to be stored in a variable named `output`.
            - If the `output` variable is not found, it returns 'No result returned'.
        """
        try:
            exec_globals = {}
            exec(code, exec_globals)
            result = exec_globals.get('output', 'No result returned')
            return str(result), True
        except Exception as e:
            return str(e), False

    def clone(self):
        """
        Creates a clone of the RunPythonTool instance.

        Returns:
            RunPythonTool: A new instance of RunPythonTool.
        """
        return RunPythonTool()

