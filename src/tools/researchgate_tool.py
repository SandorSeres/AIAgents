import scrapy
from scrapy.crawler import CrawlerProcess
import json
from scrapy.spidermiddlewares.httperror import HttpError
from bs4 import BeautifulSoup

# Globális változó az adatok tárolására
scraped_data = []

class ResearchGateSpider(scrapy.Spider):
    name = "researchgate"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Referer': 'https://www.researchgate.net/',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        },
        'HTTPERROR_ALLOWED_CODES': [403],  # Engedélyezzük a 403-as hibakódokat
        'DOWNLOAD_DELAY': 0.5,  # Késleltetés a kérések között, hogy ne legyen túl gyors
        'MEDIA_ALLOW_REDIRECTS': False,  # Ne irányítson át médiatartalom letöltése esetén
        'IMAGES_ENABLED': False,  # Képek letöltésének letiltása
    }

    def __init__(self, query_or_url, is_url=False, *args, **kwargs):
        super(ResearchGateSpider, self).__init__(*args, **kwargs)
        self.query_or_url = query_or_url
        self.is_url = is_url

    def start_requests(self):
        #  page=2
        if self.is_url:
            yield scrapy.Request(url=self.query_or_url, callback=self.parse_url, errback=self.errback_httpbin)
        else:
            search_url = f"https://www.researchgate.net/search/publication?q={self.query_or_url.replace(' ', '+')}"
            yield scrapy.Request(url=search_url, callback=self.parse_search, errback=self.errback_httpbin)

    def parse_search(self, response):
        # BeautifulSoup használata a HTML feldolgozásához
        soup = BeautifulSoup(response.text, 'html.parser')

        # Keresési eredmények feldolgozása, találatok URL-jeinek begyűjtése
        for result in soup.find_all('div', class_='nova-o-stack__item'):
            title_tag = result.find('a', class_='nova-e-link--theme-bare')
            if title_tag:
                publication_url = "https://www.researchgate.net" + title_tag['href']
                
                # Meglátogatjuk az egyes publikációk oldalát
                yield scrapy.Request(url=publication_url, callback=self.parse_publication)

    def parse_publication(self, response):
        # BeautifulSoup használata a publikáció oldalának feldolgozásához
        soup = BeautifulSoup(response.text, 'html.parser')

        # Kinyerjük az Abstractot (ha van)
        abstract_tag = soup.find('div', class_='nova-e-text--spacing-none')
        abstract = abstract_tag.get_text(strip=True) if abstract_tag else 'N/A'

        # Adatok hozzáadása a listához
        scraped_data.append({
            'publication_url': response.url,
            'abstract': abstract
        })

    def errback_httpbin(self, failure):
        # Hibakezelés, ha HTTP hiba történt
        if failure.check(HttpError):
            response = failure.value.response
            print(f"HTTP hiba történt: {response.status}, de az adatokat feldolgozom...")
            self.parse_search(response)  # Feldolgozzuk a választ, még ha 403-as is

class ResearchGateTool:
    """
    A tool for scraping academic papers from ResearchGate using a search query or a specific URL.
    """
    name: str = "ResearchGateTool"
    description: str = "A tool for scraping academic papers from ResearchGate using a search query or a specific URL."
    parameters: str = """Mandatory parameters: 
                            - query_or_url: This is the query string or an URL, 
                            - is_url: bool = True if the query_or_url is a publication URL"""

    def __init__(self):
        """
        Initializes the ResearchGateTool.
        """
        pass

    def _run(self, query_or_url: str, is_url: bool = False):
        """
        Runs the scraping process and returns the extracted data.

        Parameters:
            query_or_url (str): The search query or specific URL to scrape data from.
            is_url (bool): If True, it treats query_or_url as a URL. If False, treats it as a search query.

        Returns:
            str: The scraped data in JSON format.
        """
        global scraped_data
        scraped_data = []  # Töröljük az előző eredményeket
        process = CrawlerProcess()
        process.crawl(ResearchGateSpider, query_or_url=query_or_url, is_url=is_url)
        process.start()
        
        # Visszaadjuk az összegyűjtött adatokat JSON formátumban
        return json.dumps(scraped_data, indent=4)

    def clone(self):
        """
        Creates a clone of the ResearchGateTool instance.

        Returns:
            ResearchGateTool: A new instance of ResearchGateTool.
        """
        return ResearchGateTool()

if __name__ == "__main__":

    # Használati példa
    tool = ResearchGateTool()

    # Run with query (keresés alapján)
    query = 'machine learning in healthcare'
    scraped_data = tool._run(query_or_url=query, is_url=False)
    print(scraped_data)

    # Run with specific URL (konkrét URL alapján)
    # url = 'https://www.researchgate.net/publication/xyz'  # Helyettesítsd egy valós URL-lel
    # scraped_data = tool._run(query_or_url=url, is_url=True)
    # print(scraped_data)
