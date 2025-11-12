"""
Web Scraper Module

This module provides comprehensive web scraping functionality.
It can extract content from a main page and all its subpages within the same domain.

Features:
- Crawls main page and discovers subpages
- Extracts text content, metadata, and structure
- Respects crawl depth and page limits
- Handles errors gracefully
- Implements polite crawling with delays
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
import re

from ..utils.url_validator import URLValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedPage:
    """
    Data class to store information about a scraped page.

    Attributes:
        url (str): The URL of the page
        title (str): Page title
        content (str): Main text content
        metadata (Dict): Additional metadata (description, keywords, etc.)
        links (List[str]): List of links found on the page
        depth (int): Crawl depth level
        timestamp (float): When the page was scraped
    """
    url: str
    title: str = ""
    content: str = ""
    metadata: Dict = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    depth: int = 0
    timestamp: float = field(default_factory=time.time)


class WebScraper:
    """
    A comprehensive web scraper that extracts content from websites.

    This scraper can:
    - Crawl a website starting from a base URL
    - Extract all subpages within the same domain
    - Extract text content, titles, and metadata
    - Respect crawl depth and page limits
    - Implement polite crawling with delays
    """

    def __init__(
        self,
        max_depth: int = 3,
        max_pages: int = 50,
        timeout: int = 10,
        delay: float = 1.0,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ):
        """
        Initialize the WebScraper.

        Args:
            max_depth (int): Maximum depth for crawling subpages
            max_pages (int): Maximum number of pages to scrape
            timeout (int): Request timeout in seconds
            delay (float): Delay between requests in seconds
            user_agent (str): User agent string for requests
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.delay = delay
        self.user_agent = user_agent

        self.url_validator = URLValidator()
        self.visited_urls: Set[str] = set()
        self.scraped_pages: List[ScrapedPage] = []

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def scrape_website(self, start_url: str) -> List[ScrapedPage]:
        """
        Scrape a website starting from the given URL.

        This method performs a breadth-first crawl of the website,
        extracting content from the main page and all discoverable subpages
        within the same domain.

        Args:
            start_url (str): The starting URL to scrape

        Returns:
            List[ScrapedPage]: List of all scraped pages

        Raises:
            ValueError: If the start URL is invalid
        """
        # Validate and normalize the start URL
        normalized_url = self.url_validator.normalize_url(start_url)
        if not normalized_url:
            raise ValueError(f"Invalid URL: {start_url}")

        logger.info(f"Starting scrape of {normalized_url}")

        # Reset state
        self.visited_urls.clear()
        self.scraped_pages.clear()

        # Start crawling
        self._crawl_recursive(normalized_url, depth=0)

        logger.info(f"Scraping complete. Total pages scraped: {len(self.scraped_pages)}")
        return self.scraped_pages

    def _crawl_recursive(self, url: str, depth: int):
        """
        Recursively crawl pages starting from the given URL.

        Args:
            url (str): Current URL to crawl
            depth (int): Current crawl depth
        """
        # Check stopping conditions
        if depth > self.max_depth:
            logger.debug(f"Max depth reached for {url}")
            return

        if len(self.scraped_pages) >= self.max_pages:
            logger.info(f"Max pages ({self.max_pages}) reached")
            return

        # Clean and normalize URL
        url = self.url_validator.clean_url(url)

        # Skip if already visited
        if url in self.visited_urls:
            return

        # Mark as visited
        self.visited_urls.add(url)

        try:
            # Scrape the page
            logger.info(f"Scraping [{depth}]: {url}")
            scraped_page = self._scrape_page(url, depth)

            if scraped_page:
                self.scraped_pages.append(scraped_page)

                # Extract the base domain
                base_domain = self.url_validator.get_domain(url)

                # Find and crawl subpages
                for link in scraped_page.links:
                    # Check if we've hit the page limit
                    if len(self.scraped_pages) >= self.max_pages:
                        break

                    # Only follow links in the same domain
                    if self.url_validator.is_same_domain(url, link):
                        # Polite crawling: add delay between requests
                        time.sleep(self.delay)
                        self._crawl_recursive(link, depth + 1)

        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")

    def _scrape_page(self, url: str, depth: int) -> Optional[ScrapedPage]:
        """
        Scrape a single page and extract its content.

        Args:
            url (str): URL of the page to scrape
            depth (int): Current crawl depth

        Returns:
            Optional[ScrapedPage]: Scraped page data or None if failed
        """
        try:
            # Make the request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extract title
            title = self._extract_title(soup)

            # Extract main content
            content = self._extract_content(soup)

            # Extract metadata
            metadata = self._extract_metadata(soup)

            # Extract links
            links = self._extract_links(soup, url)

            # Create ScrapedPage object
            scraped_page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                links=links,
                depth=depth,
                timestamp=time.time()
            )

            logger.debug(f"Successfully scraped: {url} (Content length: {len(content)} chars)")
            return scraped_page

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        if soup.title:
            return soup.title.string.strip() if soup.title.string else ""

        # Try h1 as fallback
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()

        return "Untitled"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main text content from the page.

        This method removes script, style, and other non-content elements,
        then extracts and cleans the text.
        """
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """
        Extract metadata from the page (description, keywords, author, etc.).
        """
        metadata = {}

        # Extract meta tags
        meta_tags = soup.find_all('meta')

        for tag in meta_tags:
            # Get name and content
            name = tag.get('name', tag.get('property', ''))
            content = tag.get('content', '')

            if name and content:
                metadata[name] = content

        # Extract headings for structure
        headings = []
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip()
                })

        if headings:
            metadata['headings'] = headings

        return metadata

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all valid links from the page.

        Args:
            soup (BeautifulSoup): Parsed HTML
            base_url (str): Base URL for resolving relative links

        Returns:
            List[str]: List of absolute URLs
        """
        links = []

        for anchor in soup.find_all('a', href=True):
            href = anchor['href']

            # Skip anchors, javascript, mailto, etc.
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            # Make absolute URL
            absolute_url = self.url_validator.make_absolute_url(base_url, href)

            if absolute_url and absolute_url not in links:
                links.append(absolute_url)

        return links

    def get_scraped_pages(self) -> List[ScrapedPage]:
        """
        Get all scraped pages.

        Returns:
            List[ScrapedPage]: List of all scraped pages
        """
        return self.scraped_pages

    def get_scrape_summary(self) -> Dict:
        """
        Get a summary of the scraping session.

        Returns:
            Dict: Summary statistics
        """
        return {
            'total_pages': len(self.scraped_pages),
            'total_urls_visited': len(self.visited_urls),
            'max_depth_reached': max([page.depth for page in self.scraped_pages], default=0),
            'total_content_length': sum([len(page.content) for page in self.scraped_pages]),
            'unique_domains': len(set([self.url_validator.get_domain(page.url) for page in self.scraped_pages]))
        }


if __name__ == "__main__":
    # Test the scraper
    scraper = WebScraper(max_depth=2, max_pages=10, delay=1)

    try:
        pages = scraper.scrape_website("https://example.com")

        print("\n" + "=" * 60)
        print("SCRAPING SUMMARY")
        print("=" * 60)

        summary = scraper.get_scrape_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")

        print("\n" + "=" * 60)
        print("SCRAPED PAGES")
        print("=" * 60)

        for i, page in enumerate(pages[:5], 1):  # Show first 5
            print(f"\n{i}. {page.title}")
            print(f"   URL: {page.url}")
            print(f"   Depth: {page.depth}")
            print(f"   Content length: {len(page.content)} chars")
            print(f"   Links found: {len(page.links)}")

    except Exception as e:
        print(f"Error: {e}")
