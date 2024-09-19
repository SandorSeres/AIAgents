"""
File Name: microsoft_news_tool.py
Description: This file contains the implementation of the MicrosoftNewsTool class, which fetches and returns the content of search results from Microsoft's news website along with the appropriate URLs. The class is designed for simple query-response interactions.

Author: [Your Name]
Date: 2024-09-18
Version: 1.0
License: [Creative Commons Zero v1.0 Universal]
"""

import requests
from bs4 import BeautifulSoup

class MicrosoftNewsTool:
    """
    Class Name: MicrosoftNewsTool
    Description: A tool that retrieves and returns the content of search results from Microsoft's news website along with their URLs.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of the tool's functionality.
        parameters (str): The expected input parameter for the tool.

    Methods:
        _run(query):
            Fetches search results from Microsoft's news website based on the provided query and returns their content and URLs.
        
        clone():
            Returns a new instance of MicrosoftNewsTool.
    """

    name: str = "MicrosoftNewsTool"
    description: str = "A tool to fetch content of search results from Microsoft's news website and returns the found URLs and their full content."
    parameters: str = "Mandatory: query"

    def _run(self, query: str = None) -> str:
        """
        Fetches and returns the content of search results from Microsoft's news website based on the provided query.

        Parameters:
            query (str): The search query to fetch results for.

        Returns:
            str: A formatted string containing the titles, URLs, and full content of the search results.
        
        Notes:
            - This method performs an HTTP GET request to fetch search results.
            - It parses the HTML content using BeautifulSoup.
            - It handles exceptions that may occur during the request or parsing.
        """
        try:
            # Construct the search URL
            search_url = f"https://news.microsoft.com/source?s={query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            print(response)
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            print(soup)
            results = []

            # Find all article elements in the search results
            articles = soup.find_all('article')

            for article in articles[:8]:  # Limit to first 8 results
                # Find the <a> tag with a 'title' attribute
                link_tag = article.find('a', href=True, title=True)
                if link_tag:
                    url = link_tag['href']
                    # Extract the title from the 'title' attribute, removing the prefix
                    title_attr = link_tag['title']
                    title = title_attr.replace('View post ', '').strip()
                else:
                    continue  # Skip if link not found

                # Fetch each article's content
                article_response = requests.get(url, headers=headers)
                article_response.raise_for_status()
                article_soup = BeautifulSoup(article_response.text, 'html.parser')

                # Extract the article content
                content_div = article_soup.find('div', class_='article-body')
                if not content_div:
                    # Try alternative class if 'article-body' is not found
                    content_div = article_soup.find('div', class_='post-body')

                if content_div:
                    content = content_div.get_text(separator='\n', strip=True)
                else:
                    content = 'No content available.'

                results.append(f"Title: {title}\nURL: {url}\nContent:\n{content}\n{'-'*80}\n")

            if results:
                return '\n'.join(results), True
            else:
                return "No results found for your query.", False

        except requests.exceptions.RequestException as e:
            return f"An error occurred while fetching the search results: {e}", False

    def clone(self):
        """
        Creates a clone of the MicrosoftNewsTool instance.

        Returns:
            MicrosoftNewsTool: A new instance of MicrosoftNewsTool.
        """
        return MicrosoftNewsTool()
