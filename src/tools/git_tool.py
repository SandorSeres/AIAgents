"""
File Name: git_tool.py
Description: This file defines the GitCloneTool class, which provides functionalities to clone a GitHub repository into a specified directory using authentication and return the list of downloaded files. The class supports filtering the downloaded files by their extension.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import os
import subprocess
import json
import shutil

class GitCloneTool:
    """
    Class Name: GitCloneTool
    Description: GitCloneTool is a utility class designed to clone GitHub repositories into a specified directory using a Personal Access Token (PAT) for authentication. It can return the list of downloaded files, optionally filtered by file extension.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (list): A list of parameters required by the tool, including the repository URL, directory, token, and file extension.

    Methods:
        clone_repository(repository_url, directory, token):
            Clones the specified GitHub repository into the provided directory using the given authentication token.
        
        _get_downloaded_files(directory, file_extension):
            Retrieves the list of files in the cloned repository, optionally filtered by file extension.
        
        _run(repository_url, directory, token, file_extension):
            Executes the cloning process and returns the list of files, optionally filtered by file extension.
        
        clone():
            Returns a new instance of GitCloneTool.
    """
    
    name: str = "GitCloneTool"
    description: str = "A tool to clone a GitHub repository into a specified directory with authentication and return the path list of the downloaded files."
    parameters: list = ["repository_url", "directory", "token", "file_extension"]

    def clone_repository(self, repository_url: str, directory: str, token: str) -> tuple:
        """
        Clones the GitHub repository to the specified directory using an authentication token.

        Parameters:
            repository_url (str): The URL of the GitHub repository to clone.
            directory (str): The directory where the repository should be cloned.
            token (str): GitHub Personal Access Token (PAT) for authentication.

        Returns:
            tuple: A tuple containing a success message, the list of downloaded files, and a task_completed flag, or an error message if cloning fails.
        
        Notes:
            - The method inserts the token into the repository URL to facilitate authentication.
            - If the directory exists, it is cleared before cloning.
            - Returns a tuple with a success message or an error message and a flag indicating the success of the operation.
        """
        # Insert token into the repository URL for authentication
        if repository_url.startswith("https://"):
            auth_repo_url = repository_url.replace("https://", f"https://{token}@")
        else:
            return "Invalid repository URL format. Use https://", [], False
        
        # Clear the directory if it exists
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

        command = ["git", "clone", auth_repo_url, directory]
        try:
            subprocess.run(command, check=True)
            # After successful cloning, return success message
            return f"Repository cloned into {directory}.", True
        except subprocess.CalledProcessError as e:
            return f"Error cloning repository: {str(e)}", False

    def _get_downloaded_files(self, directory: str, file_extension: str = None) -> list:
        """
        Retrieves the list of all files downloaded into the specified directory after cloning.

        Parameters:
            directory (str): The directory where the repository was cloned.
            file_extension (str): The file extension to filter by (e.g., '.py'). Defaults to None, which means no filtering.

        Returns:
            list: A list of paths to all the files in the cloned repository, optionally filtered by file extension.
        
        Notes:
            - The method traverses the directory tree to collect all file paths.
            - If a file extension is provided, only files with that extension are included in the list.
        """
        files_list = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file_extension:
                    if file.endswith(file_extension):
                        files_list.append(os.path.join(root, file))
                else:
                    files_list.append(os.path.join(root, file))
        return files_list

    def _run(self, repository_url: str, directory: str, token: str, file_extension: str = None) -> tuple:
        """
        Clones a repository using a token and returns the list of downloaded files, optionally filtered by file extension.

        Parameters:
            repository_url (str): The URL of the GitHub repository to clone.
            directory (str): The directory where the repository should be cloned.
            token (str): GitHub Personal Access Token (PAT) for authentication.
            file_extension (str): The file extension to filter by (e.g., '.py'). Defaults to None.

        Returns:
            tuple: A tuple containing a message, the list of downloaded files (filtered by extension), and a success flag.
        
        Notes:
            - The method first calls `clone_repository` to clone the repository.
            - If the cloning is successful, it retrieves the list of downloaded files.
            - The files can be filtered by their extension if specified.
        """
        clone_message, clone_success = self.clone_repository(repository_url, directory, token)
        print(clone_message)
        if clone_success:
            files_list = self._get_downloaded_files(directory, file_extension)
            return f"Solution: {files_list}", True
        else:
            return f"Solution: []", True

    def clone(self):
        """
        Creates a clone of the GitCloneTool instance.

        Returns:
            GitCloneTool: A new instance of GitCloneTool.
        """
        return GitCloneTool()


# Example usage:
if __name__ == "__main__":
    tool = GitCloneTool()
    repo_url = os.getenv('GITHUB_REPOSITORY_URL')
    directory = "./clone"
    token = os.getenv('GITHUB_TOKEN')  # GitHub token
    file_extension = ".py"  # Only return Python files

    message, files_list, success = tool._run(repo_url, directory, token, file_extension)
    if success:
        print("Clone successful!")
        print("Downloaded files:", files_list)
    else:
        print("Error:", message)

