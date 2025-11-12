"""
URL Validator Utility

This module provides functionality to validate and normalize URLs.
It ensures that URLs are properly formatted and accessible before scraping.
"""

import re
import validators
from urllib.parse import urlparse, urljoin
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLValidator:
    """
    A utility class for validating and processing URLs.

    This class provides methods to:
    - Validate URL format
    - Normalize URLs
    - Extract domain information
    - Check if URLs belong to the same domain
    """

    def __init__(self):
        """Initialize the URLValidator."""
        pass

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if a URL is valid and well-formed.

        Args:
            url (str): The URL to validate

        Returns:
            bool: True if URL is valid, False otherwise

        Example:
            >>> validator = URLValidator()
            >>> validator.is_valid_url("https://example.com")
            True
            >>> validator.is_valid_url("not-a-url")
            False
        """
        if not url or not isinstance(url, str):
            return False

        # Use validators library for basic validation
        if not validators.url(url):
            return False

        # Additional checks
        parsed = urlparse(url)

        # Must have scheme (http/https)
        if parsed.scheme not in ['http', 'https']:
            return False

        # Must have netloc (domain)
        if not parsed.netloc:
            return False

        return True

    @staticmethod
    def normalize_url(url: str) -> Optional[str]:
        """
        Normalize a URL by adding scheme if missing and removing fragments.

        Args:
            url (str): The URL to normalize

        Returns:
            Optional[str]: Normalized URL or None if invalid

        Example:
            >>> validator = URLValidator()
            >>> validator.normalize_url("example.com")
            'https://example.com'
        """
        if not url:
            return None

        url = url.strip()

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Parse and reconstruct URL without fragment
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if parsed.query:
            normalized += f"?{parsed.query}"

        # Validate the normalized URL
        if URLValidator.is_valid_url(normalized):
            return normalized

        return None

    @staticmethod
    def get_domain(url: str) -> Optional[str]:
        """
        Extract the domain (netloc) from a URL.

        Args:
            url (str): The URL to extract domain from

        Returns:
            Optional[str]: Domain name or None if invalid

        Example:
            >>> validator = URLValidator()
            >>> validator.get_domain("https://www.example.com/page")
            'www.example.com'
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc if parsed.netloc else None
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return None

    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain.

        Args:
            url1 (str): First URL
            url2 (str): Second URL

        Returns:
            bool: True if same domain, False otherwise

        Example:
            >>> validator = URLValidator()
            >>> validator.is_same_domain(
            ...     "https://example.com/page1",
            ...     "https://example.com/page2"
            ... )
            True
        """
        domain1 = URLValidator.get_domain(url1)
        domain2 = URLValidator.get_domain(url2)

        if not domain1 or not domain2:
            return False

        return domain1 == domain2

    @staticmethod
    def is_absolute_url(url: str) -> bool:
        """
        Check if a URL is absolute (has scheme and netloc).

        Args:
            url (str): The URL to check

        Returns:
            bool: True if absolute URL, False otherwise
        """
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)

    @staticmethod
    def make_absolute_url(base_url: str, relative_url: str) -> Optional[str]:
        """
        Convert a relative URL to an absolute URL using a base URL.

        Args:
            base_url (str): The base URL
            relative_url (str): The relative URL

        Returns:
            Optional[str]: Absolute URL or None if invalid

        Example:
            >>> validator = URLValidator()
            >>> validator.make_absolute_url(
            ...     "https://example.com/page",
            ...     "/about"
            ... )
            'https://example.com/about'
        """
        try:
            absolute = urljoin(base_url, relative_url)
            return absolute if URLValidator.is_valid_url(absolute) else None
        except Exception as e:
            logger.error(f"Error making absolute URL: {str(e)}")
            return None

    @staticmethod
    def clean_url(url: str) -> str:
        """
        Clean a URL by removing trailing slashes and normalizing.

        Args:
            url (str): The URL to clean

        Returns:
            str: Cleaned URL
        """
        url = url.strip()
        # Remove trailing slash unless it's the root
        if url.endswith('/') and url.count('/') > 3:
            url = url[:-1]
        return url


if __name__ == "__main__":
    # Test the URLValidator
    validator = URLValidator()

    test_urls = [
        "https://example.com",
        "example.com",
        "not-a-url",
        "https://example.com/page#section",
    ]

    print("URL Validator Tests:")
    print("-" * 50)

    for test_url in test_urls:
        print(f"\nOriginal: {test_url}")
        print(f"Valid: {validator.is_valid_url(test_url)}")
        print(f"Normalized: {validator.normalize_url(test_url)}")
        print(f"Domain: {validator.get_domain(test_url)}")
