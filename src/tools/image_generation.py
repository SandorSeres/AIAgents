"""
File Name: image_generation.py
Description: This file defines the ImageGenerationTool class, which provides functionalities to generate images based on provided text content and a specified style. The class utilizes OpenAI's image generation API and includes methods to handle retries, download the generated images, and save them to a specified location.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""
import openai
from openai import OpenAI
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
import logging
import os

# Load environment variables from the .env file
load_dotenv()

class ImageGenerationTool:
    """
    Class Name: ImageGenerationTool
    Description: A utility class designed to generate images from text descriptions using OpenAI's image generation API (such as DALL-E) and download them to a specified path. The class includes retry mechanisms for handling API errors.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (dict): A dictionary of parameters required by the tool, including text, image_style, and path.

    Methods:
        generate_image_from_text(text, image_style):
            Generates an image based on the provided text and style using OpenAI's API, with retry logic for handling API errors.
        
        download_image(url, path):
            Downloads the generated image from the provided URL and saves it to the specified path.
        
        _run(text, image_style, path):
            Executes the image generation and downloading process, returning a result message and task completion flag.
        
        clone():
            Returns a new instance of ImageGenerationTool.
    """
    
    name: str = "ImageGenerationTool"
    description: str = "Tool to generate images based on provided text content using the provided image_style."
    parameters: dict = {
        "text": "the base text to generate the image",
        "image_style": "The style definition for the generated image",
        "path": "the path to save the image"
    }

    @retry(
        stop=stop_after_attempt(3),  # Maximum three attempts
        wait=wait_exponential(min=1, max=10),  # Exponentially increasing wait between 1 and 10 seconds
        retry=retry_if_exception_type(openai.OpenAIError)  # Retry only on OpenAIError exceptions
    )
    def generate_image_from_text(self, text: str, image_style: str) -> str:
        """
        Generates an image based on the provided text and style using OpenAI's API.

        Parameters:
            text (str): The text description for the image.
            image_style (str): The style definition for the generated image.

        Returns:
            str: The URL of the generated image.

        Raises:
            openai.OpenAIError: If there is an error with the OpenAI API, the method retries up to three times.
        
        Notes:
            - This method uses retry logic to handle temporary issues with the OpenAI API.
            - The method logs the image generation prompt and returns the URL of the generated image.
        """
        client = OpenAI()
        prompt = f"{text} using the style {image_style}"
        logging.info(f"Image generation prompt: {prompt}")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url

    def download_image(self, url: str, path: str) -> tuple:
        """
        Downloads the generated image from the provided URL and saves it to the specified path.

        Parameters:
            url (str): The URL of the image to download.
            path (str): The path where the image will be saved.

        Returns:
            tuple: A tuple containing a success message or an error message and a task_completed flag.
        
        Notes:
            - The method checks the HTTP status code to ensure the image was successfully retrieved before saving it.
        """
        response = requests.get(url)
        logging.info(f"Downloading image from {url} to {path}")

        if response.status_code == 200:
            directory = os.path.dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(path, "wb") as file:
                file.write(response.content)
            return "Image downloaded successfully.", True
        else:
            return "Failed to download image.", False

    def _run(self, text: str, image_style: str, path: str) -> str:
        """
        Executes the image generation and downloading process, returning a result message and task completion flag.

        Parameters:
            text (str): The text description for the image.
            image_style (str): The style definition for the generated image.
            path (str): The path where the generated image will be saved.

        Returns:
            str: A result message indicating success or failure, and the task completion flag.
        
        Notes:
            - The method first generates the image URL and then attempts to download and save the image.
            - If an exception occurs, the method returns an error message.
        """
        try:
            image_url = self.generate_image_from_text(text, image_style)
            download_message, task_completed = self.download_image(image_url, path)
            result = f"Solution: {download_message} The image downloaded to: {path}"
            task_completed = True
        except Exception as e:
            result = f"An error occurred: {str(e)}"
            task_completed = False
        return result, task_completed

    def clone(self):
        """
        Creates a clone of the ImageGenerationTool instance.

        Returns:
            ImageGenerationTool: A new instance of ImageGenerationTool.
        """
        return ImageGenerationTool()

