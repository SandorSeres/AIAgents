"""
File Name: search_tool.py
Description: This file contains the implementation of the SearchAndRetrieveTool class, which is used to perform Google searches, retrieve the content from URLs, and convert HTML content to Markdown format. It also includes a base class, BaseSearchTool, that provides common functionality for search operations.
Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import urllib.parse
import html2text
from transformers import pipeline
import numpy as np
import logging
from  tools.file_tool import *
class BaseSearchTool:
    """
    Class Name: BaseSearchTool
    Description: BaseSearchTool provides fundamental search functionalities, including performing Google searches and retrieving web content. It serves as a base class for more specialized search tools.

    Methods:
        google_search(query, url_file, country, language, geolocation, results_per_page, date_range):
            Performs a Google search or loads URLs from a file, returning search results as a list of dictionaries.
        
        retrieve_content(url):
            Retrieves and returns the textual content of a webpage given its URL.
        
        html_to_markdown(html_string):
            Converts HTML content to Markdown format.
    """

    def google_search(self, query: List[str] = None, url_file: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, geolocation: Optional[str] = None, results_per_page: Optional[int] = 5, date_range: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Performs a Google search or loads URLs from a file, returning search results.

        Parameters:
            query (List[str]): A list of search queries to execute.
            url_file (Optional[str]): A file containing URLs to be loaded instead of performing a search.
            country (Optional[str]): A country code to limit search results to a specific country.
            language (Optional[str]): A language code to limit search results to a specific language.
            geolocation (Optional[str]): A geolocation parameter for more localized search results.
            results_per_page (Optional[int]): Number of search results to return per page (default is 5).
            date_range (Optional[str]): Limits the search results to a specific date range ('w' for last week, 'm' for last month, 'y' for last year).

        Returns:
            List[Dict[str, str]]: A list of search results, each containing a title, link, and snippet.

        Logs:
            Info: When the search starts and finishes successfully.
            Error: If there is an issue with the search or loading URLs from a file.
        """
        logging.info("Starting Google search...")
        if url_file:
            try:
                with open(url_file, 'r') as file:
                    urls = file.readlines()
                urls = [url.strip() for url in urls if url.strip()]
                search_results = [{'title': '', 'link': url, 'snippet': ''} for url in urls]
                logging.info(f"Loaded URLs from file: {url_file}")
                return search_results
            except Exception as e:
                logging.error(f"Error reading url_file: {str(e)}")
                return []
        elif query:
            if isinstance(query, str):
                query = [query]
            if not isinstance(query[0], str):
                raise TypeError("Query must be a list of str")

            params = {"q": query[0]}
            if country:
                params["cr"] = f"country{country}"
            if language:
                params["hl"] = language
            if geolocation:
                params["uule"] = geolocation
            if results_per_page:
                params["num"] = results_per_page
            if date_range:
                params["tbs"] = f"qdr:{date_range}"

            encoded = urllib.parse.urlencode(params)
            search_url = f"https://www.google.com/search?{encoded}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()
                logging.info(f"Google search successful for query: {query}")
            except requests.RequestException as e:
                logging.error(f"Google search failed: {str(e)}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            for g in soup.find_all('div', class_='g')[:results_per_page]:  # Limit to the specified results_per_page
                title = g.find('h3')
                if title:
                    link = g.find('a')['href']
                    snippet = g.find('span', class_='aCOpRe')
                    search_results.append({
                        'title': title.get_text(),
                        'link': link,
                        'snippet': snippet.get_text() if snippet else ''
                    })
            logging.info(f"Google search returned {len(search_results)} results")
            return search_results
        else:
            raise ValueError("Either query list or url_file must be provided")

    def retrieve_content(self, url: str) -> str:
        """
        Retrieves the textual content of a webpage given its URL.

        Parameters:
            url (str): The URL of the webpage to retrieve content from.

        Returns:
            str: The content of the webpage.

        Logs:
            Info: When content is successfully retrieved.
            Error: If there is a timeout or request error while retrieving the content.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        timeout_duration = 10  # Timeout duration in seconds
        try:
            response = requests.get(url, headers=headers, timeout=timeout_duration)
            response.raise_for_status()
            logging.info(f"Successfully retrieved content from URL: {url}")
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out for URL: {url}")
            return "Request timed out"
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL: {url} with error: {str(e)}")
            return f"An error occurred: {str(e)}"

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        return content

    def html_to_markdown(self, html_string):
        """
        Converts HTML content to Markdown format.

        Parameters:
            html_string (str): The HTML content to convert.

        Returns:
            str: The converted Markdown content.
        """
        if html_string and len(html_string) > 0:
            soup = BeautifulSoup(html_string, 'html.parser')
            h = html2text.HTML2Text()
            h.ignore_links = False  # Keep the links in the output
            markdown = h.handle(str(soup))
        else:
            markdown = "# Empty"
        return markdown

class SearchAndRetrieveTool(BaseSearchTool):
    """
    Class Name: SearchAndRetrieveTool
    Description: This class extends the BaseSearchTool to provide more specific functionality, including searching the internet and retrieving content from found URLs. It also converts the retrieved content into Markdown format for further processing or display.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool, including optional settings like country, language, and date range.

    Methods:
        _run(query, url_file, country, language, geolocation, results_per_page, date_range):
            Executes the search and retrieval process, returning the content in Markdown format along with the URLs.

        clone():
            Returns a new instance of SearchAndRetrieveTool with the same configuration.
    """
    name: str = "SearchAndRetrieveTool"
    description: str = "Searches the internet and returns the found URLs and their full content."
    parameters: str = "Mandatory: query, Optional: url_file, country, language, geolocation, results_per_page, date_range (e.g., 'w' for last week, 'm' for last month, 'y' for last year)"

    def _run(self, query: str = None, url_file: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, geolocation: Optional[str] = None, results_per_page: Optional[int] = 10, date_range: Optional[str] = None) -> Dict[str, str]:
        """
        Executes the search and retrieval process, returning the content in Markdown format along with the URLs.

        Parameters:
            query (str): The search query.
            url_file (Optional[str]): A file containing URLs to process instead of performing a search.
            country (Optional[str]): A country code to limit search results to a specific country.
            language (Optional[str]): A language code to limit search results to a specific language.
            geolocation (Optional[str]): A geolocation parameter for more localized search results.
            results_per_page (Optional[int]): Number of search results to return per page (default is 10).
            date_range (Optional[str]): Limits the search results to a specific date range ('w' for last week, 'm' for last month, 'y' for last year).

        Returns:
            Dict[str, str]: A dictionary containing the full content of the search results in Markdown format and the task completion status.

        Logs:
            Info: When the search and retrieval task starts and completes.
        """
        logging.info(f"Running SearchAndRetrieveTool with query: {query}")
        if url_file:
            search_results = self.google_search(url_file=url_file, country=country, language=language, geolocation=geolocation, results_per_page=results_per_page, date_range=date_range)
        else:
            search_results = self.google_search(query, country=country, language=language, geolocation=geolocation, results_per_page=results_per_page, date_range=date_range)

        search_results = self.google_search(query, url_file, country, language, geolocation, results_per_page, date_range)
        results = []
        for result in search_results:
            content = self.retrieve_content(result['link'])
            if len(content) > 0:
                results.append({
                    'url': result['link'],
                    'content': self.html_to_markdown(content)
                })
        full_content = f"The result of my research is in the next json list with the source url and the content in each finding:\n\n {str(results)}"
        task_completed = True if results else False
        logging.info(f"SearchAndRetrieveTool task completed: {task_completed}")
        return full_content, task_completed

    def clone(self):
        """
        Creates a clone of the SearchAndRetrieveTool instance.

        Returns:
            SearchAndRetrieveTool: A new instance of SearchAndRetrieveTool.
        """
        return SearchAndRetrieveTool()

class SearchRetrieveAndSaveTool(SearchAndRetrieveTool, SaveToFileTool):
    """
    Class Name: SearchRetrieveAndSaveTool
    Description: This class combines the functionality of searching, retrieving content, and saving the content to a file.
    
    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool, including query, filename, directory, and optional settings like country, language, and date range.
    
    Methods:
        _run(query, directory, filename, url_file, country, language, geolocation, results_per_page, date_range):
            Executes the search, retrieves the content, and saves the result to the specified file in the given directory.
        
        clone():
            Returns a new instance of SearchRetrieveAndSaveTool with the same configuration.
    """
    name: str = "SearchRetrieveAndSaveTool"
    description: str = "Searches the internet, retrieves content, and saves the result to a file in a specified directory."
    parameters: str = "Mandatory: query, directory , filename, Optional: url_file, country, language, geolocation, results_per_page, date_range (e.g., 'w' for last week, 'm' for last month, 'y' for last year)"

    def _run(self, query: str = None, directory: str = None, filename: str = None, url_file: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, geolocation: Optional[str] = None, results_per_page: Optional[int] = 10, date_range: Optional[str] = None) -> tuple:
        """
        Executes the search, retrieves the content, and saves the result to the specified file in the given directory.

        Parameters:
            query (str): The search query.
            directory (str): The directory where the file should be saved.
            filename (str): The name of the file to save the content to.
            url_file (Optional[str]): A file containing URLs to process instead of performing a search.
            country (Optional[str]): A country code to limit search results to a specific country.
            language (Optional[str]): A language code to limit search results to a specific language.
            geolocation (Optional[str]): A geolocation parameter for more localized search results.
            results_per_page (Optional[int]): Number of search results to return per page (default is 10).
            date_range (Optional[str]): Limits the search results to a specific date range ('w' for last week, 'm' for last month, 'y' for last year).

        Returns:
            tuple: A tuple containing the file path or an error message if an exception occurs, along with a task_completed flag.
        """
        # Perform the search and retrieve content
        search_results, task_completed = super()._run(query, url_file, country, language, geolocation, results_per_page, date_range)
        
        if task_completed:
            # Save the retrieved content to a file
            save_result, save_completed = SaveToFileTool()._run(txt=search_results, filename=filename, directory=directory)
            return save_result, save_completed
        else:
            return "Search and retrieve process failed.", False

    def clone(self):
        """
        Creates a clone of the SearchRetrieveAndSaveTool instance.

        Returns:
            SearchRetrieveAndSaveTool: A new instance of SearchRetrieveAndSaveTool.
        """
        return SearchRetrieveAndSaveTool()
