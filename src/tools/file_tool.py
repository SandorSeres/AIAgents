"""
File Name: file_tool.py
Description: This file contains the implementation of two utility classes: ReadFileTool and SaveToFileTool. These classes provide simple interfaces for reading from and writing to files within specified directories. They are designed to handle file operations safely and efficiently.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import os

class ReadFileTool:
    """
    Class Name: ReadFileTool
    Description: A utility class designed to read the content of a specified file from a given directory. This tool does not support wildcard usage and requires explicit filenames.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (list): A list of parameters required by the tool, including the filename and directory.

    Methods:
        _run(filename, directory):
            Reads the content of the specified file from the given directory and returns the content or an error message.
        
        clone():
            Returns a new instance of ReadFileTool.
    """

    name: str = "ReadFileTool"
    description: str = "A tool to read one file from specified directory with given filenames. No wildcard usage possible."
    parameters: list = ["filename", "directory"]

    def _run(self, filename: str, directory: str) -> tuple:
        """
        Reads the content of a specified file from the given directory.

        Parameters:
            filename (str): The name of the file to read.
            directory (str): The directory where the file is located.

        Returns:
            tuple: A tuple containing the file content if the file exists, or an error message if the file does not exist, along with a task_completed flag.
        
        Notes:
            - The method checks if the file exists in the specified directory.
            - If the file exists, it reads and returns its content; otherwise, it returns an error message.
        """
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            with open(path, "r") as file:
                content = file.read()
                return content, True
        else:
            return f"{path} does not exist.", False

    def clone(self):
        """
        Creates a clone of the ReadFileTool instance.

        Returns:
            ReadFileTool: A new instance of ReadFileTool.
        """
        return ReadFileTool()

class SaveToFileTool:
    """
    Class Name: SaveToFileTool
    Description: A utility class designed to save generated content to a specified file within a given directory. It ensures that the directory exists before saving the file.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (list): A list of parameters required by the tool, including the content to save, filename, and directory.

    Methods:
        _run(txt, filename, directory):
            Saves the provided content to a file in the specified directory and returns the file path or an error message.
        
        clone():
            Returns a new instance of SaveToFileTool.
    """

    name: str = "SaveToFileTool"
    description: str = "A tool to save generated content to a specified directory with given filenames."
    parameters: list = ["txt", "filename", "directory"]

    def _run(self, txt: str, filename: str, directory: str) -> tuple:
        """
        Saves the provided content to a specified file within a given directory.

        Parameters:
            txt (str): The content to save to the file.
            filename (str): The name of the file to save the content to.
            directory (str): The directory where the file should be saved.

        Returns:
            tuple: A tuple containing a success message with the file path or an error message if an exception occurs, along with a task_completed flag.
        
        Notes:
            - The method ensures that the specified directory exists before attempting to save the file.
            - The content is saved to the file in write mode, which overwrites any existing file with the same name.
        """
        print(f"Save it in {directory} as {filename}")
        try:
            # Ensure the directory exists
            os.makedirs(directory, exist_ok=True)
            # Define the file path
            file_path = os.path.join(directory, filename)
            # Write the content to the file
            with open(file_path, 'w') as file:
                print(txt, file=file)
            return f"Solution: {file_path}", True
        except Exception as e:
            return f"An error occurred: {str(e)}", False

    def clone(self):
        """
        Creates a clone of the SaveToFileTool instance.

        Returns:
            SaveToFileTool: A new instance of SaveToFileTool.
        """
        return SaveToFileTool()

