"""
File Name: search_tool.py
Description: This file contains the implementation of various search tools that perform searches, retrieve content from URLs, and convert HTML content to Markdown format. It includes a base class, BaseSearchTool, that provides common functionality for search operations, and specialized classes like SearchAndRetrieveTool, SearchRetrieveAndSaveTool, CoreSearchRetrieveAndSaveTool, MicrosoftNewsSearchRetrieveAndSaveTool, PubMedSearchRetrieveAndSaveTool, and WikipediaSearchRetrieveAndSaveTool.

This version includes multithreading to parallelize searches and content retrievals for better performance, and common functionalities have been extracted into the base class to reduce code duplication.

Author: [Sandor Seres (sseres@code.hu)]
Date: 2024-08-31
Version: 1.8
License: [Creative Commons Zero v1.0 Universal]
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import urllib.parse
import html2text
import logging
from tools.file_tool import AppendToFileTool  # Ensure this import is correct
from itertools import zip_longest
import os  # To access environment variables
from Bio import Entrez
import time
import random
import json
import httpx  # For asynchronous HTTP requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class BaseSearchTool:
    """
    Class Name: BaseSearchTool
    Description: BaseSearchTool provides fundamental search functionalities, including performing Google searches, CORE API searches, and retrieving web content. It serves as a base class for more specialized search tools. Common methods like 'retrieve_and_convert_content' have been implemented here to avoid code duplication.

    Methods:
        google_search(query, url_file, country, language, geolocation, results_per_page, date_range):
            Performs a Google search or loads URLs from a file, returning search results as a list of dictionaries.

        core_search(query, results_per_page):
            Performs a search using the CORE API.

        retrieve_content(url):
            Retrieves and returns the textual content of a webpage given its URL.

        html_to_markdown(html_string):
            Converts HTML content to Markdown format.

        retrieve_and_convert_content(url):
            Retrieves content from a URL and converts it to Markdown.

        limit_word_count(text, max_words):
            Limits the word count of the text to a specified maximum.
    """

    def google_search(self, query: Optional[str] = None, url_file: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, geolocation: Optional[str] = None, results_per_page: Optional[int] = 5, date_range: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Performs a Google search or loads URLs from a file, returning search results.

        Parameters:
            query (Optional[str]): A search query to execute.
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
            if not isinstance(query, str):
                raise TypeError("Query must be a string")

            params = {"q": query}
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
                logging.error(f"Google search failed for query '{query}': {str(e)}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            for g in soup.find_all('div', class_='g')[:results_per_page]:
                title = g.find('h3')
                if title:
                    link = g.find('a')['href']
                    snippet = g.find('span', class_='aCOpRe')
                    search_results.append({
                        'title': title.get_text(),
                        'link': link,
                        'snippet': snippet.get_text() if snippet else ''
                    })
            logging.info(f"Google search returned {len(search_results)} results for query: {query}")
            return search_results
        else:
            raise ValueError("Either a single query or url_file must be provided")

    def core_search(self, query: str, results_per_page: Optional[int] = 10) -> List[Dict[str, str]]:
        """
        Performs a search using the CORE API.

        Parameters:
            query (str): Search query.
            results_per_page (Optional[int]): Number of search results to return per query (default is 10).

        Returns:
            List[Dict[str, str]]: A list of search results, each containing a title, link, and snippet.
        """
        endpoint = 'https://api.core.ac.uk/v3/search/works'
        CORE_API_KEY = os.getenv('CORE_API_KEY')
        if not CORE_API_KEY:
            logging.error("CORE_API_KEY environment variable not set.")
            raise ValueError("CORE_API_KEY environment variable not set.")

        params = {
            'q': query,
            'limit': results_per_page,
            'apiKey': CORE_API_KEY
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            search_results = []
            for item in data.get('results', []):
                title = item.get('title', 'No title')
                # Determine the link
                link = None
                if 'urls' in item and item['urls']:
                    link = item['urls'][0]
                elif 'downloadUrl' in item and item['downloadUrl']:
                    link = item['downloadUrl']
                elif 'sourceFulltextUrls' in item and item['sourceFulltextUrls']:
                    link = item['sourceFulltextUrls'][0]
                else:
                    link = None
                snippet = item.get('abstract', 'No abstract available')
                search_results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
            logging.info(f"CORE API search successful for query: {query}")
            return search_results
        except requests.RequestException as e:
            logging.error(f"CORE API search failed for query '{query}': {str(e)}")
            return []

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
            "User-Agent": "Mozilla/5.0"
        }
        timeout_duration = 10  # Timeout duration in seconds
        logging.info(f"Retrieving URL: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=timeout_duration)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            logging.info(f"Successfully retrieved content from URL: {url}")
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out for URL: {url}")
            return "Request timed out"
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL: {url} with error: {str(e)}")
            return f"An error occurred: {str(e)}"

        if 'application/pdf' in content_type:
            # Process PDF
            try:
                from io import BytesIO
                from PyPDF2 import PdfReader

                pdf_content = BytesIO(response.content)
                reader = PdfReader(pdf_content)
                text = ''
                for page in reader.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text
                return text
            except Exception as e:
                logging.error(f"Error processing PDF content from URL: {url} with error: {str(e)}")
                return f"An error occurred processing PDF: {str(e)}"
        else:
            # Process HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text() for p in paragraphs])
            return content

    def html_to_markdown(self, html_string: str) -> str:
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

    def retrieve_and_convert_content(self, url: str) -> Optional[str]:
        """
        Retrieves content from a URL and converts it to Markdown.

        Parameters:
            url (str): The URL to retrieve content from.

        Returns:
            Optional[str]: The content in Markdown format, or None if retrieval failed.
        """
        content = self.retrieve_content(url)
        if content and content != "Request timed out" and not content.startswith("An error occurred"):
            markdown_content = self.html_to_markdown(content)
            return markdown_content
        else:
            return None

    def limit_word_count(self, text: str, max_words: int) -> str:
        """
        Limits the word count of the text to a specified maximum.

        Parameters:
            text (str): The text to limit.
            max_words (int): The maximum number of words.

        Returns:
            str: The text limited to the specified number of words.
        """
        words = text.split()
        if len(words) > max_words:
            limited_words = words[:max_words]
            return ' '.join(limited_words) + '... [Content truncated]'
        else:
            return text


class SearchAndRetrieveTool(BaseSearchTool):
    """
    Class Name: SearchAndRetrieveTool
    Description: This class extends the BaseSearchTool to provide more specific functionality, including searching the internet and retrieving content from found URLs. It also converts the retrieved content into Markdown format for further processing or display.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool, including optional settings like country, language, and date range.

    Methods:
        _run(queries, url_file, languages, country, geolocation, results_per_page, date_range):
            Executes the search and retrieval process, returning the content in Markdown format along with the URLs.

        clone():
            Returns a new instance of SearchAndRetrieveTool with the same configuration.
    """
    name: str = "SearchAndRetrieveTool"
    description: str = "Searches the internet and returns the found URLs and their full content."
    parameters: str = "Mandatory: queries (list of queries), languages (list of language codes). Optional: url_file, country, geolocation, results_per_page, date_range (e.g., 'w' for last week, 'm' for last month, 'y' for last year)"

    def _run(
        self,
        queries: List[str] = None,
        url_file: Optional[str] = None,
        languages: List[str] = None,
        country: Optional[str] = None,
        geolocation: Optional[str] = None,
        results_per_page: Optional[int] = 10,
        date_range: Optional[str] = None,
    ) -> Tuple[str, bool]:
        """
        Executes the search and retrieval process for multiple queries and languages.

        Parameters:
            queries (List[str]): List of search queries.
            url_file (Optional[str]): A file containing URLs to process instead of performing a search.
            languages (List[str]): List of language codes corresponding to each query.
            country (Optional[str]): A country code to limit search results to a specific country.
            geolocation (Optional[str]): A geolocation parameter for more localized search results.
            results_per_page (Optional[int]): Number of search results to return per page (default is 10).
            date_range (Optional[str]): Limits the search results to a specific date range ('w' for last week, 'm' for last month, 'y' for last year).

        Returns:
            Tuple[str, bool]: A tuple containing the combined content and the task completion status.
        """
        logging.info(f"Running SearchAndRetrieveTool with queries: {queries} and languages: {languages}")

        if not queries or len(queries) == 0:
            raise ValueError("At least one query must be provided")
        if not languages or len(languages) == 0:
            raise ValueError("At least one language must be provided")

        if len(queries) != len(languages):
            # Adjust the length of the two lists
            min_length = min(len(queries), len(languages))
            queries = queries[:min_length]
            languages = languages[:min_length]

        # Collect search results for each query using multithreading
        all_search_results = []
        with ThreadPoolExecutor() as executor:
            future_to_search = {
                executor.submit(
                    self.google_search,
                    query=query,
                    country=country,
                    language=language,
                    geolocation=geolocation,
                    results_per_page=results_per_page,
                    date_range=date_range
                ): (query, language)
                for query, language in zip(queries, languages)
            }
            for future in as_completed(future_to_search):
                query, language = future_to_search[future]
                try:
                    results = future.result()
                    all_search_results.append(results)
                except Exception as e:
                    logging.error(f"Search failed for query '{query}' with error: {str(e)}")
                    all_search_results.append([])

        # Reorganize results
        interleaved_results = []
        for result_tuple in zip_longest(*all_search_results):
            for result in result_tuple:
                if result is not None:
                    interleaved_results.append(result)

        # Deduplicate results based on URLs
        unique_results = {}
        for result in interleaved_results:
            url = result['link']
            if url not in unique_results:
                unique_results[url] = result

        logging.info(f"URLs:\n {unique_results}\n")

        # Retrieve content using multithreading
        results_with_content = []
        with ThreadPoolExecutor() as executor:
            future_to_url = {
                executor.submit(self.retrieve_and_convert_content, url=result['link']): result['link']
                for result in unique_results.values()
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    if content:
                        results_with_content.append({
                            "url": f"""{url}""",
                            "content": f"""{content}"""
                        })
                except Exception as e:
                    logging.error(f"Failed to retrieve content from {url} with error: {str(e)}")

        if not results_with_content:
            logging.warning("No valid content retrieved from the search results.")
            full_content = "No valid content retrieved from the search results."
            task_completed = False
        else:
            full_content = f"The result of my research is in the next JSON list with the source URL and the content in each finding:\n\n{json.dumps(results_with_content, indent=4)}"
            task_completed = True

        logging.info(f"SearchAndRetrieveTool task completed: {task_completed}")
        return full_content, task_completed

    def clone(self):
        """
        Creates a clone of the SearchAndRetrieveTool instance.

        Returns:
            SearchAndRetrieveTool: A new instance of SearchAndRetrieveTool.
        """
        return SearchAndRetrieveTool()


class SearchRetrieveAndSaveTool(SearchAndRetrieveTool):
    """
    Class Name: SearchRetrieveAndSaveTool
    Description: This class combines the functionality of searching, retrieving content, and saving the content to a file.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool, including query, filename, directory, and optional settings like country, language, and date range.

    Methods:
        _run(queries, directory, filename, url_file, languages, country, geolocation, results_per_page, date_range):
            Executes the search, retrieves the content, and saves the result to the specified file in the given directory.

        clone():
            Returns a new instance of SearchRetrieveAndSaveTool with the same configuration.
    """
    name: str = "SearchRetrieveAndSaveTool"
    description: str = "Searches the internet, retrieves content, and saves the result to a file in a specified directory."
    parameters: str = "Mandatory: queries (list of queries), languages (list of language codes), directory (str), filename (str). Optional: url_file, country, geolocation, results_per_page, date_range (e.g., 'w' for last week, 'm' for last month, 'y' for last year)"

    def _run(
        self,
        queries: List[str] = None,
        directory: str = None,
        filename: str = None,
        url_file: Optional[str] = None,
        languages: Optional[List[str]] = None,
        country: Optional[str] = None,
        geolocation: Optional[str] = None,
        results_per_page: Optional[int] = 10,
        date_range: Optional[str] = None,
        search_engine: str = 'google'
    ) -> Tuple[str, bool]:
        """
        Executes the search, retrieves the content, and saves the result to the specified file in the given directory.

        Parameters:
            queries (List[str]): The search query list.
            directory (str): The directory where the file should be saved.
            filename (str): The name of the file to save the content to.
            url_file (Optional[str]): A file containing URLs to process instead of performing a search.
            languages (Optional[List[str]]): A list of language codes corresponding to each query.
            country (Optional[str]): A country code to limit search results to a specific country.
            geolocation (Optional[str]): A geolocation parameter for more localized search results.
            results_per_page (Optional[int]): Number of search results to return per page (default is 10).
            date_range (Optional[str]): Limits the search results to a specific date range ('w' for last week, 'm' for last month, 'y' for last year).

        Returns:
            Tuple[str, bool]: A tuple containing the file path or an error message if an exception occurs, along with a task_completed flag.
        """
        logging.info(f"Running SearchRetrieveAndSaveTool with queries: {queries} and languages: {languages}")

        if not directory:
            raise ValueError("A directory must be provided")
        if not filename:
            raise ValueError("A filename must be provided")

        # Perform the search and retrieve content
        try:
            search_results, task_completed = super()._run(
                queries=queries,
                url_file=url_file,
                languages=languages,
                country=country,
                geolocation=geolocation,
                results_per_page=results_per_page,
                date_range=date_range
            )
        except Exception as e:
            logging.error(f"Error during search and retrieve: {str(e)}")
            return f"An error occurred during search and retrieve: {str(e)}", False

        if task_completed:
            try:
                # Save the retrieved content to a file
                save_result, save_completed = AppendToFileTool()._run(txt=search_results, filename=filename, directory=directory)
                if save_completed:
                    logging.info(f"Content successfully saved to {save_result}")
                    return f"Content successfully saved to {save_result}", True
                else:
                    logging.error("Failed to save content to file.")
                    return "Failed to save content to file.", False
            except Exception as e:
                logging.error(f"Error during saving to file: {str(e)}")
                return f"An error occurred during saving to file: {str(e)}", False
        else:
            logging.warning("Search and retrieve process failed.")
            return "Search and retrieve process failed.", False

    def clone(self):
        """
        Creates a clone of the SearchRetrieveAndSaveTool instance.

        Returns:
            SearchRetrieveAndSaveTool: A new instance of SearchRetrieveAndSaveTool.
        """
        return SearchRetrieveAndSaveTool()


class CoreSearchRetrieveAndSaveTool(BaseSearchTool):
    """
    Class Name: CoreSearchRetrieveAndSaveTool
    Description: This class specializes in searching academic works using the CORE API, retrieving content, and saving the result to a file.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool.

    Methods:
        _run(queries, directory, filename, results_per_page):
            Executes the search on the CORE API, retrieves the content, and saves it to the specified file.

        clone():
            Returns a new instance of CoreSearchRetrieveAndSaveTool with the same configuration.
    """
    name: str = "CoreSearchRetrieveAndSaveTool"
    description: str = "Searches academic works using the CORE API, retrieves content, and saves the result to a file in a specified directory."
    parameters: str = "Mandatory: queries (list of queries), directory (str), filename (str). Optional: results_per_page"

    def _run(
        self,
        queries: List[str] = None,
        directory: str = None,
        filename: str = None,
        results_per_page: Optional[int] = 10
    ) -> Tuple[str, bool]:
        logging.info(f"Running CoreSearchRetrieveAndSaveTool with queries: {queries}")

        if not queries or len(queries) == 0:
            raise ValueError("At least one query must be provided")
        if not directory:
            raise ValueError("A directory must be provided")
        if not filename:
            raise ValueError("A filename must be provided")

        # Collect search results for each query using multithreading
        all_search_results = []
        with ThreadPoolExecutor() as executor:
            future_to_query = {
                executor.submit(self.core_search, query=query, results_per_page=results_per_page): query
                for query in queries
            }
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    all_search_results.append(results)
                except Exception as e:
                    logging.error(f"CORE search failed for query '{query}' with error: {str(e)}")
                    all_search_results.append([])

        # Interleave the results
        interleaved_results = []
        for result_tuple in zip_longest(*all_search_results):
            for result in result_tuple:
                if result is not None:
                    interleaved_results.append(result)

        # Deduplicate results based on URLs
        unique_results = {}
        for result in interleaved_results:
            url = result['link']
            if url and url not in unique_results:
                unique_results[url] = result

        logging.info(f"URLs:\n {unique_results}\n")

        # Retrieve content using multithreading
        results_with_content = []
        with ThreadPoolExecutor() as executor:
            future_to_url = {}
            for result in unique_results.values():
                if result['link']:
                    future = executor.submit(self.retrieve_and_convert_content, url=result['link'])
                    future_to_url[future] = result['link']
                else:
                    # Use the snippet as content if there's no direct link
                    markdown_content = self.html_to_markdown(result['snippet'])
                    results_with_content.append({
                        "url": "No direct link",
                        "content": f"""{markdown_content}"""
                    })
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    if content:
                        results_with_content.append({
                            "url": f"""{url}""",
                            "content": f"""{content}"""
                        })
                except Exception as e:
                    logging.error(f"Failed to retrieve content from {url} with error: {str(e)}")

        if not results_with_content:
            logging.warning("No valid content retrieved from the search results.")
            full_content = "No valid content retrieved from the search results."
            task_completed = False
        else:
            full_content = f"The result of my research is in the next JSON list with the source URL and the content in each finding:\n\n{json.dumps(results_with_content, indent=4)}"
            task_completed = True

        if task_completed:
            try:
                # Save the retrieved content to a file
                save_result, save_completed = AppendToFileTool()._run(txt=full_content, filename=filename, directory=directory)
                if save_completed:
                    logging.info(f"Content successfully saved to {save_result}")
                    return f"Content successfully saved to {save_result}", True
                else:
                    logging.error("Failed to save content to file.")
                    return "Failed to save content to file.", False
            except Exception as e:
                logging.error(f"Error during saving to file: {str(e)}")
                return f"An error occurred during saving to file: {str(e)}", False
        else:
            logging.warning("Search and retrieve process failed.")
            return "Search and retrieve process failed.", False

    def clone(self):
        """
        Creates a clone of the CoreSearchRetrieveAndSaveTool instance.

        Returns:
            CoreSearchRetrieveAndSaveTool: A new instance of CoreSearchRetrieveAndSaveTool.
        """
        return CoreSearchRetrieveAndSaveTool()


class MicrosoftNewsSearchRetrieveAndSaveTool(BaseSearchTool):
    """
    Class Name: MicrosoftNewsSearchRetrieveAndSaveTool
    Description: This class searches Microsoft's news website, retrieves content, and saves the result to a file in a specified directory.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool.

    Methods:
        _run(query, directory, filename):
            Executes the search, retrieves the content, and saves the result to the specified file in the given directory.

        clone():
            Returns a new instance of MicrosoftNewsSearchRetrieveAndSaveTool with the same configuration.
    """
    name: str = "MicrosoftNewsSearchRetrieveAndSaveTool"
    description: str = "Searches Microsoft's news website, retrieves content, and saves the result to a file in a specified directory."
    parameters: str = "Mandatory: queries (list of queries), directory (str), filename (str)"

    def _run(self, queries: List[str] = None, directory: str = None, filename: str = None) -> Tuple[str, bool]:
        """
        Executes the search, retrieves the content, and saves the result to the specified file in the given directory.

        Parameters:
            queries (List[str]): List of search queries to fetch results for.
            directory (str): The directory where the file should be saved.
            filename (str): The name of the file to save the content to.

        Returns:
            Tuple[str, bool]: A tuple containing the file path or an error message if an exception occurs, along with a task_completed flag.
        """
        logging.info(f"Running MicrosoftNewsSearchRetrieveAndSaveTool with queries: {queries}")

        if not queries or len(queries) == 0:
            raise ValueError("At least one query must be provided")
        if not directory:
            raise ValueError("A directory must be provided")
        if not filename:
            raise ValueError("A filename must be provided")

        results = []

        with ThreadPoolExecutor() as executor:
            future_to_query = {
                executor.submit(self.process_query, query): query for query in queries
            }

            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    query_results = future.result()
                    if query_results:
                        results.extend(query_results)
                except Exception as e:
                    logging.error(f"Error processing query '{query}': {str(e)}")

        if results:
            # Convert the list to JSON
            full_content = f"The result of my research is in the next JSON list with the source URL and the content in each finding:\n\n{json.dumps(results, indent=4)}"
 
            # Save the retrieved content to a file
            try:
                save_result, save_completed = AppendToFileTool()._run(txt=full_content, filename=filename, directory=directory)
                if save_completed:
                    logging.info(f"Content successfully saved to {save_result}")
                    return f"Content successfully saved to {save_result}", True
                else:
                    logging.error("Failed to save content to file.")
                    return "Failed to save content to file.", False
            except Exception as e:
                logging.error(f"Error during saving to file: {str(e)}")
                return f"An error occurred during saving to file: {str(e)}", False
        else:
            logging.warning("No results found for your queries.")
            return "No results found for your queries.", False

    def process_query(self, query: str) -> List[Dict[str, str]]:
        """
        Processes a single query by searching Microsoft's news website and retrieving content.

        Parameters:
            query (str): The search query.

        Returns:
            List[Dict[str, str]]: A list of results for the query.
        """
        logging.info(f"Processing query: {query}")

        try:
            # Construct the search URL
            search_url = f"https://news.microsoft.com/source?s={urllib.parse.quote(query)}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')

            query_results = []
            with ThreadPoolExecutor() as executor:
                future_to_article = {}
                for article in articles[:8]:  # Limit to first 8 results per query
                    # Find the <a> tag with a 'title' attribute
                    link_tag = article.find('a', href=True, title=True)
                    if link_tag:
                        url = link_tag['href']
                        # Extract the title from the 'title' attribute, removing the prefix
                        title_attr = link_tag['title']
                        title = title_attr.replace('View post ', '').strip()
                        # Schedule retrieval of article content
                        future = executor.submit(self.retrieve_and_convert_content, url)
                        future_to_article[future] = {'title': title, 'url': url}
                    else:
                        continue  # Skip if link not found

                for future in as_completed(future_to_article):
                    article_info = future_to_article[future]
                    try:
                        content = future.result()
                        if content:
                            query_results.append({
                                "title": f"""{article_info['title']}""",
                                "url": f"""{article_info['url']}""",
                                "content": f"""{content}"""
                            })
                    except Exception as e:
                        logging.error(f"Error fetching content for {article_info['url']}: {str(e)}")

            return query_results

        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while fetching the search results for query '{query}': {e}")
            return []

    def clone(self):
        """
        Creates a clone of the MicrosoftNewsSearchRetrieveAndSaveTool instance.

        Returns:
            MicrosoftNewsSearchRetrieveAndSaveTool: A new instance of MicrosoftNewsSearchRetrieveAndSaveTool.
        """
        return MicrosoftNewsSearchRetrieveAndSaveTool()


class PubMedSearchRetrieveAndSaveTool(BaseSearchTool):
    """
    Class Name: PubMedSearchRetrieveAndSaveTool
    Description: This class searches PubMed for articles, retrieves abstracts and full content in markdown format, and saves the result to a file.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (str): The parameters that can be passed to the tool.

    Methods:
        _run(search_terms, mindate, maxdate, retmax, directory, filename):
            Executes the PubMed search, retrieves content, and saves the result to the specified file.

        clone():
            Returns a new instance of PubMedSearchRetrieveAndSaveTool with the same configuration.
    """
    name: str = "PubMedSearchRetrieveAndSaveTool"
    description: str = "Searches PubMed for articles, retrieves abstracts and full content, and saves the result to a file in a specified directory."
    parameters: str = "Mandatory: queries (list of search terms in PubMed standard format), directory (str), filename (str). Optional : mindate (str), maxdate (str), retmax (int)"

    def __init__(self):
        Entrez.email = 'sas@code.hu'

    def _run(
        self,
        queries: List[str] = None,
        directory: str = None,
        filename: str = None,
        mindate: Optional[str] = None,
        maxdate: Optional[str] = None,
        retmax: Optional[int] = 10
    ) -> Tuple[str, bool]:
        """
        Executes the PubMed search, retrieves content, and saves the result to the specified file.

        Parameters:
            search_terms (List[str]): List of search terms for PubMed.
            mindate (str): The minimum publication date (YYYY/MM/DD).
            maxdate (str): The maximum publication date (YYYY/MM/DD).
            directory (str): The directory where the file should be saved.
            filename (str): The name of the file to save the content to.
            retmax (int): The maximum number of articles to retrieve per search term.

        Returns:
            Tuple[str, bool]: A tuple containing the file path or an error message if an exception occurs, along with a task_completed flag.
        """
        logging.info(f"Running PubMedSearchRetrieveAndSaveTool with search_terms: {queries}")

        if not queries or len(queries) == 0:
            raise ValueError("At least one search term must be provided")
        # if not mindate:
        #     raise ValueError("A mindate must be provided")
        # if not maxdate:
        #     raise ValueError("A maxdate must be provided")
        if not directory:
            raise ValueError("A directory must be provided")
        if not filename:
            raise ValueError("A filename must be provided")

        articles = []

        with ThreadPoolExecutor() as executor:
            future_to_search = {
                executor.submit(self.perform_pubmed_search, term, mindate, maxdate, retmax): term
                for term in queries
            }
            for future in as_completed(future_to_search):
                term = future_to_search[future]
                try:
                    term_articles = future.result()
                    articles.extend(term_articles)
                except Exception as e:
                    logging.error(f"Error processing search term '{term}': {str(e)}")

        if not articles:
            logging.warning("No articles found for the provided search terms.")
            return "No articles found for the provided search terms.", False

        # Convert the list to JSON
        full_content = f"The result of my research is in the next JSON list with the source URL and the content in each finding:\n\n{json.dumps(articles, indent=4)}"

        # Save the retrieved content to a file
        try:
            save_result, save_completed = AppendToFileTool()._run(txt=full_content, filename=filename, directory=directory)
            if save_completed:
                logging.info(f"Content successfully saved to {save_result}")
                return f"Content successfully saved to {save_result}", True
            else:
                logging.error("Failed to save content to file.")
                return "Failed to save content to file.", False
        except Exception as e:
            logging.error(f"Error during saving to file: {str(e)}")
            return f"An error occurred during saving to file: {str(e)}", False

    def perform_pubmed_search(
        self,
        search_term: str,
        mindate: str,
        maxdate: str,
        retmax: int=10,
    ) -> List[Dict[str, str]]:
        """
        Performs a PubMed search for a single search term and retrieves articles.

        Parameters:
            search_term (str): The search term for PubMed.
            mindate (str): The minimum publication date (YYYY/MM/DD).
            maxdate (str): The maximum publication date (YYYY/MM/DD).
            retmax (int): The maximum number of articles to retrieve.
            language_filter (str): Language filter for the search.

        Returns:
            List[Dict[str, str]]: A list of articles with their details.
        """
        logging.info(f"Performing PubMed search for term: {search_term}")

        try:
            # Construct the search query
            query = search_term
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=retmax,
                mindate=mindate,
                maxdate=maxdate,
                usehistory="y",  # Use history for large result sets
            )
            record = Entrez.read(handle)
            handle.close()

            pmid_list = record.get("IdList", [])
            if not pmid_list:
                logging.warning(f"No articles found for search term: {search_term}")
                return []

            # Fetch articles and metadata using WebEnv and QueryKey for large queries
            webenv = record["WebEnv"]
            query_key = record["QueryKey"]
            handle = Entrez.efetch(
                db="pubmed",
                rettype="xml",
                retmode="xml",
                webenv=webenv,
                query_key=query_key,
                retstart=0,          # Start at the first record
                retmax=retmax,       # Retrieve up to 'retmax' records
            )
            records = Entrez.read(handle)
            handle.close()

            term_articles = []

            with ThreadPoolExecutor() as executor:
                future_to_record = {
                    executor.submit(self.process_pubmed_article, record): record
                    for record in records.get("PubmedArticle", [])
                }
                time.sleep(5)

                for future in as_completed(future_to_record):
                    record = future_to_record[future]
                    try:
                        article_data = future.result()
                        term_articles.append(article_data)
                    except Exception as e:
                        pmid = record["MedlineCitation"]["PMID"]
                        logging.error(
                            f"Failed to process article PMID {pmid} with error: {str(e)}"
                        )

            return term_articles

        except Exception as e:
            logging.error(
                f"An error occurred during PubMed search for term '{search_term}': {str(e)}"
            )
            return []

    def process_pubmed_article(self, record) -> Dict[str, str]:
        """
        Processes a single PubMed article record.

        Parameters:
            record: The PubMed article record.

        Returns:
            Dict[str, str]: The article data including PMID, Title, Abstract, Publisher Link, and Content.
        """
        try:
            time.sleep(random.randint(1, 5))
            pmid = str(record["MedlineCitation"]["PMID"])
            title = record["MedlineCitation"]["Article"].get("ArticleTitle", "No title available")

            # Extract the abstract
            abstract = "No abstract available"
            article = record["MedlineCitation"]["Article"]
            if "Abstract" in article:
                abstract_text = article["Abstract"].get("AbstractText", "")
                if isinstance(abstract_text, list):
                    # Join multiple abstract sections
                    abstract = " ".join(str(section) for section in abstract_text)
                elif isinstance(abstract_text, str):
                    abstract = abstract_text
                else:
                    abstract = str(abstract_text)

            # Extract the DOI
            doi = None
            for article_id in record["PubmedData"]["ArticleIdList"]:
                if article_id.attributes.get("IdType") == "doi":
                    doi = str(article_id)
                    break
            publisher_link = f"https://doi.org/{doi}" if doi else "No DOI available"

            # Retrieve content from the publisher link if DOI exists
            content = self.retrieve_and_convert_content(publisher_link) if doi else ""
            if not content or len(content)  == 0 :
                if abstract :
                    content = abstract
            # Combine data into a dictionary
            article_data = {
                "PMID": f"""{pmid}""",
                "title": f"""{title}""",
                "abstract": f"""{abstract}""",
                "url": f"""{publisher_link}""",
                "content": f"""{content}""",
            }
            return article_data

        except Exception as e:
            logging.error(f"An error occurred while processing article record: {str(e)}")
            raise

    def clone(self):
        """
        Creates a clone of the PubMedSearchRetrieveAndSaveTool instance.

        Returns:
            PubMedSearchRetrieveAndSaveTool: A new instance of PubMedSearchRetrieveAndSaveTool.
        """
        return PubMedSearchRetrieveAndSaveTool()


class WikipediaSearchRetrieveAndSaveTool(BaseSearchTool):
    """
    Class Name: WikipediaSearchRetrieveAndSaveTool
    Description: Searches Wikipedia and returns full markdown content and a summary of a Wikipedia page, then saves it to a file.
    
    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of the tool's functionality.
        parameters (str): The expected input parameters for the tool.
    
    Methods:
        _run(queries, directory, filename):
            Searches Wikipedia for the queries and saves the content and summary to a file.
    
        clone():
            Returns a new instance of WikipediaSearchRetrieveAndSaveTool.
    """
    name: str = "WikipediaSearchRetrieveAndSaveTool"
    description: str = "Searches Wikipedia and saves full markdown content and a summary of a Wikipedia page to a file."
    parameters: str = "Mandatory: queries (list of queries), directory (str), filename (str)"

    def _run(self, queries: List[str] = None, directory: str = None, filename: str = None) -> Tuple[str, bool]:
        """
        Searches Wikipedia for the queries and saves the content and summary to a file.

        Parameters:
            queries (List[str]): List of search queries.
            directory (str): The directory where the file should be saved.
            filename (str): The name of the file.

        Returns:
            Tuple[str, bool]: A tuple containing the file path or an error message, along with a task_completed flag.
        """
        logging.info(f"Running WikipediaSearchRetrieveAndSaveTool with queries: {queries}")

        if not queries or len(queries) == 0:
            raise ValueError("At least one query must be provided")
        if not directory:
            raise ValueError("A directory must be provided")
        if not filename:
            raise ValueError("A filename must be provided")

        results = []

        with ThreadPoolExecutor() as executor:
            future_to_query = {
                executor.submit(self.process_query, query): query for query in queries
            }

            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    query_results = future.result()
                    if query_results:
                        results.extend(query_results)
                except Exception as e:
                    logging.error(f"Error processing query '{query}': {str(e)}")

        if results:
            # Convert the list to JSON
            full_content = f"The result of my research is in the next JSON list with the source URL and the content in each finding:\n\n{json.dumps(results, indent=4)}"
            task_completed = True

            # Save the retrieved content to a file
            try:
                save_result, save_completed = AppendToFileTool()._run(txt=full_content, filename=filename, directory=directory)
                if save_completed:
                    logging.info(f"Content successfully saved to {save_result}")
                    return f"Content successfully saved to {save_result}", True
                else:
                    logging.error("Failed to save content to file.")
                    return "Failed to save content to file.", False
            except Exception as e:
                logging.error(f"Error during saving to file: {str(e)}")
                return f"An error occurred during saving to file: {str(e)}", False
        else:
            logging.warning("No results found for your queries.")
            return "No results found for your queries.", False

    def process_query(self, query: str) -> List[Dict[str, str]]:
        """
        Processes a single query by searching Wikipedia and retrieving content.

        Parameters:
            query (str): The search query.

        Returns:
            List[Dict[str, str]]: A list of results for the query.
        """
        logging.info(f"Processing query: {query}")

        try:
            # Search Wikipedia pages matching the query
            search_response = httpx.get("https://en.wikipedia.org/w/api.php", params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            }, follow_redirects=True).json()

            if not search_response.get("query", {}).get("search"):
                logging.warning(f"No Wikipedia pages found for query: {query}")
                return []

            # Get the first result's title
            page_title = search_response["query"]["search"][0]["title"]

            # Get the full Wikipedia page content
            page_response = httpx.get(f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}", follow_redirects=True)
            
            # Ellenőrizzük, hogy a válasz sikeres volt-e
            if page_response.status_code != 200:
                logging.error(f"Failed to retrieve page for title '{page_title}'. HTTP Status: {page_response.status_code}")
                return []

            page_content_html = page_response.text
            markdown_content = self.html_to_markdown(page_content_html)

            # Limit content to max 15,000 words
            filtered_markdown_content = self.limit_word_count(markdown_content, max_words=15000)

            # Get the summary of the page from the Wikipedia REST API
            summary_response = httpx.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}", follow_redirects=True)

            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                summary = summary_data.get("extract", "No summary available")
            else:
                summary = "No summary available"

            result = {
                "title": page_title,
                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}",
                "summary": f"""{summary}""",
                "content": f"""{filtered_markdown_content}"""
            }

            return [result]

        except Exception as e:
            logging.error(f"An error occurred while processing query '{query}': {str(e)}")
            return []

    def html_to_markdown(self, html_string: str) -> str:
        """
        Converts full HTML to Markdown.

        Parameters:
            html_string (str): The HTML content to convert.

        Returns:
            str: The converted Markdown content.
        """
        # Parse the HTML
        soup = BeautifulSoup(html_string, 'html.parser')

        # Target the main content area of the Wikipedia page
        content_div = soup.find(id="mw-content-text")  # Target the main content

        if content_div:
            # Remove unwanted elements like references, images, and metadata
            for tag in content_div.find_all(['sup', 'table', 'img', 'style', 'script', 'footer', 'nav', 'aside']):
                tag.decompose()  # Remove these tags

            # Convert filtered content to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False  # Keep links
            markdown = h.handle(str(content_div))

            return markdown if markdown.strip() else "# Content not available"
        else:
            return "# Content not available"

    def clone(self):
        """
        Creates a clone of the WikipediaSearchRetrieveAndSaveTool instance.

        Returns:
            WikipediaSearchRetrieveAndSaveTool: A new instance of WikipediaSearchRetrieveAndSaveTool.
        """
        return WikipediaSearchRetrieveAndSaveTool()


# def main():
#     # Inicializáljuk a PubMed toolt
#     pubmed_tool = PubMedSearchRetrieveAndSaveTool()
    
#     # Definiáljuk a keresési kifejezéseket
#     pubmed_search_terms = [
#         "Machine Learning",
#         "Genomics",
#         "Neuroscience"
#     ]
    
#     # Definiáljuk a dátumtartományt (YYYY/MM/DD formátumban)
#     mindate = "2023/01/01"
#     maxdate = "2023/12/31"
    
#     # Definiáljuk a mentési könyvtárat és fájlnevet
#     pubmed_directory = "./"
#     pubmed_filename = "pubmed_content.json"
    
#     # Futtatjuk a toolt
#     results, success = pubmed_tool._run(
#         search_terms=pubmed_search_terms,
#         mindate=mindate,
#         maxdate=maxdate,
#         directory=pubmed_directory,
#         filename=pubmed_filename,
#         retmax=5  # Maximális cikkek száma keresési kifejezésenként
#     )
    
#     # Kiírjuk az eredményeket
#     if success:
#         print(f"Eredmények sikeresen mentve a következő helyre: {results}")
#     else:
#         print(f"Hiba történt a keresés vagy mentés során: {results}")

# main()



# tool = WikipediaSearchRetrieveAndSaveTool()

# # Define a search query for testing
# query = ["Latest advancements in AI technology"]

# # Run the tool with the test query
# results, success = tool._run(query, directory="./", filename="sas.txt")
