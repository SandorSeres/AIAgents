from parsel import Selector
from playwright.sync_api import sync_playwright
import json
import time  # For adding delays
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def scrape_researchgate_articles(query: str):
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()

        articles = []
        page_num = 1

        while True:
            print(f"Extracting Page: {page_num}")
            page.goto(f"https://www.researchgate.net/search/publication?q={query}&page={page_num}")
            page.wait_for_load_state("networkidle")  # Wait for the page to load completely
            selector = Selector(text=page.content())

            article_divs = selector.css(".nova-legacy-c-card__body--spacing-inherit")

            if not article_divs:
                break  # No more articles

            for article in article_divs:
                title = article.css(".nova-legacy-e-link--theme-bare::text").get()
                article_relative_url = article.css(".nova-legacy-e-link--theme-bare::attr(href)").get()
                
                # Ensure the relative URL starts with a slash
                if not article_relative_url.startswith('/'):
                    article_relative_url = '/' + article_relative_url
                
                article_url = f'https://www.researchgate.net{article_relative_url}'

                # Remove query parameters from the article URL
                parsed_url = urlparse(article_url)
                article_url_no_query = urlunparse(parsed_url._replace(query=''))

                # Visit the article page to get the abstract/content
                article_page = context.new_page()
                try:
                    article_page.goto(article_url_no_query)
                    article_page.wait_for_load_state("networkidle")
                    time.sleep(2)  # Wait for potential dynamic content to load

                    # Extract the page content
                    article_content = article_page.content()
                    article_selector = Selector(text=article_content)

                    # Attempt to extract the abstract using various selectors
                    abstract = None

                    # Try different possible selectors for the abstract
                    abstract_selectors = [
                        ".research-detail__abstract .nova-e-text",  # Current abstract container
                        ".nova-c-card__body .nova-e-text",          # Alternative container
                        ".publication-abstract",                    # Older layout
                        ".js-target-abstract .nova-e-text"          # JavaScript-rendered content
                    ]

                    for abs_selector in abstract_selectors:
                        abstract = article_selector.css(abs_selector).xpath('string()').get()
                        if abstract:
                            abstract = ' '.join(abstract.split())
                            break  # Stop if abstract is found

                    # Handle cases where abstract is behind a "Read More" button
                    if not abstract:
                        # Check for "Read More" button and click it
                        read_more_button = article_page.query_selector("button[aria-controls='abstract-full']")
                        if read_more_button:
                            read_more_button.click()
                            article_page.wait_for_timeout(1000)  # Wait for content to expand
                            # Re-extract the content
                            article_content = article_page.content()
                            article_selector = Selector(text=article_content)
                            for abs_selector in abstract_selectors:
                                abstract = article_selector.css(abs_selector).xpath('string()').get()
                                if abstract:
                                    abstract = ' '.join(abstract.split())
                                    break

                    # Improved abstract extraction using BeautifulSoup
                        if not abstract:
                            # Use Playwright to get the full page content
                            page_html = article_page.content()
                            soup = BeautifulSoup(page_html, 'html.parser')

                            # Attempt to find the main content area
                            main_content = soup.find('div', {'class': 'js-target-research-detail'})

                            if main_content:
                                text_content = main_content.get_text(separator=' ', strip=True)
                            else:
                                # Fallback to extracting all text
                                text_content = soup.get_text(separator=' ', strip=True)

                            # Assign the text content to abstract
                            abstract = text_content
                            # Optionally, limit the length of abstract to avoid excessively long texts
                            abstract = abstract[:1000] + '...' if len(abstract) > 1000 else abstract

                                    # Use Playwright to get the full page content
                        page_html = article_page.content()
                        soup = BeautifulSoup(page_html, 'html.parser')


                except Exception as e:
                    print(f"Error accessing {article_url_no_query}: {e}")
                    abstract = None
                finally:
                    article_page.close()

                # Itt illeszd be a BeautifulSoup-pal történő abstract kinyerést
                articles.append({
                    "title": title,
                    "url": article_url_no_query,
                    "abstract": abstract
                })
            
            # Check if there is a 'next' button to navigate to the next page
            next_button = selector.css(".nova-legacy-c-button-group__item a[rel='next']")
            if next_button:
                page_num += 1
            else:
                break

        # Output the results in JSON format
        print(json.dumps(articles, indent=2, ensure_ascii=False))

        browser.close()

#scrape_researchgate_articles(query="coffee")
