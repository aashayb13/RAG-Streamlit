# Web Scraper Module

## Overview

The Web Scraper module provides comprehensive functionality for extracting content from websites, including automatic discovery and crawling of subpages within the same domain.

## Features

- **Breadth-First Crawling**: Systematically explores website structure
- **Subpage Discovery**: Automatically finds and scrapes linked pages
- **Domain Restriction**: Only follows links within the same domain
- **Polite Crawling**: Configurable delays between requests
- **Content Extraction**: Extracts text, titles, metadata, and links
- **Error Handling**: Gracefully handles timeouts and HTTP errors
- **Progress Tracking**: Monitors scraping progress and statistics

## Architecture

### Main Components

#### 1. ScrapedPage (Data Class)
Stores information about each scraped page:
- `url`: Page URL
- `title`: Page title
- `content`: Extracted text content
- `metadata`: Additional metadata (descriptions, keywords, headings)
- `links`: List of links found on the page
- `depth`: Crawl depth level
- `timestamp`: When the page was scraped

#### 2. WebScraper (Main Class)
The core scraper that orchestrates the crawling process.

## Usage

### Basic Usage

```python
from src.scraper.web_scraper import WebScraper

# Initialize scraper
scraper = WebScraper(
    max_depth=3,      # How deep to crawl
    max_pages=50,     # Maximum pages to scrape
    timeout=10,       # Request timeout in seconds
    delay=1.0         # Delay between requests
)

# Scrape a website
pages = scraper.scrape_website("https://example.com")

# Access scraped data
for page in pages:
    print(f"Title: {page.title}")
    print(f"URL: {page.url}")
    print(f"Content length: {len(page.content)} chars")
    print(f"Links found: {len(page.links)}")
    print(f"Depth: {page.depth}")
    print("-" * 50)
```

### Advanced Usage

```python
from src.scraper.web_scraper import WebScraper

# Custom configuration
scraper = WebScraper(
    max_depth=5,
    max_pages=100,
    timeout=15,
    delay=2.0,
    user_agent="MyBot/1.0"
)

# Scrape website
pages = scraper.scrape_website("https://example.com")

# Get summary statistics
summary = scraper.get_scrape_summary()
print(f"Total pages: {summary['total_pages']}")
print(f"Max depth reached: {summary['max_depth_reached']}")
print(f"Total content: {summary['total_content_length']} chars")
```

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_depth` | int | 3 | Maximum depth for crawling subpages |
| `max_pages` | int | 50 | Maximum number of pages to scrape |
| `timeout` | int | 10 | Request timeout in seconds |
| `delay` | float | 1.0 | Delay between requests (in seconds) |
| `user_agent` | str | Mozilla/5.0... | User agent string for requests |

### Best Practices

1. **Start Small**: Begin with low `max_pages` (e.g., 10) for testing
2. **Be Polite**: Use at least 1 second delay between requests
3. **Respect Limits**: Don't set `max_pages` too high on first run
4. **Check robots.txt**: Ensure you're allowed to scrape the site
5. **Monitor Progress**: Watch for timeouts and adjust accordingly

## How It Works

### Crawling Process

```
1. Start URL
   ↓
2. Validate & Normalize URL
   ↓
3. Fetch Page
   ↓
4. Extract Content
   ├── Title
   ├── Text Content
   ├── Metadata
   └── Links
   ↓
5. Filter Links (same domain only)
   ↓
6. Add to Queue
   ↓
7. Repeat for each link
   (until max_depth or max_pages reached)
```

### Content Extraction

The scraper intelligently extracts content by:
1. Removing script, style, nav, and footer elements
2. Extracting text from the remaining HTML
3. Cleaning up whitespace and formatting
4. Preserving paragraph structure

### Metadata Extraction

Extracted metadata includes:
- Meta tags (description, keywords, author, etc.)
- Open Graph tags
- Heading structure (h1-h6)
- Page attributes

## Methods

### Main Methods

#### `scrape_website(start_url: str) -> List[ScrapedPage]`
Scrapes a website starting from the given URL.

**Parameters:**
- `start_url` (str): The starting URL to scrape

**Returns:**
- `List[ScrapedPage]`: List of all scraped pages

**Raises:**
- `ValueError`: If the start URL is invalid

#### `get_scraped_pages() -> List[ScrapedPage]`
Returns all scraped pages.

**Returns:**
- `List[ScrapedPage]`: List of all scraped pages

#### `get_scrape_summary() -> Dict`
Returns summary statistics about the scraping session.

**Returns:**
- `Dict`: Dictionary with statistics:
  - `total_pages`: Number of pages scraped
  - `total_urls_visited`: Total URLs visited
  - `max_depth_reached`: Maximum depth reached
  - `total_content_length`: Total characters scraped
  - `unique_domains`: Number of unique domains

### Internal Methods

- `_crawl_recursive(url: str, depth: int)`: Recursively crawl pages
- `_scrape_page(url: str, depth: int)`: Scrape a single page
- `_extract_title(soup: BeautifulSoup)`: Extract page title
- `_extract_content(soup: BeautifulSoup)`: Extract main content
- `_extract_metadata(soup: BeautifulSoup)`: Extract metadata
- `_extract_links(soup: BeautifulSoup, base_url: str)`: Extract links

## Error Handling

The scraper handles various error scenarios:

1. **Invalid URLs**: Validates and normalizes URLs before scraping
2. **Request Timeouts**: Catches and logs timeout errors
3. **HTTP Errors**: Handles 404, 500, etc. gracefully
4. **Parsing Errors**: Continues if a page fails to parse
5. **Network Issues**: Logs and continues to next page

## Limitations

- **Same Domain Only**: Only follows links within the same domain
- **JavaScript**: Cannot execute JavaScript (only static HTML)
- **Authentication**: No support for login-required pages
- **Rate Limiting**: Basic delay-based rate limiting only
- **Dynamic Content**: Cannot scrape content loaded via JavaScript

## Examples

### Example 1: Simple Scraping

```python
from src.scraper.web_scraper import WebScraper

scraper = WebScraper(max_depth=2, max_pages=10)
pages = scraper.scrape_website("https://example.com")

for page in pages:
    print(f"{page.title} - {page.url}")
```

### Example 2: Export to JSON

```python
import json
from src.scraper.web_scraper import WebScraper

scraper = WebScraper()
pages = scraper.scrape_website("https://example.com")

# Convert to JSON
pages_dict = []
for page in pages:
    pages_dict.append({
        'url': page.url,
        'title': page.title,
        'content': page.content,
        'depth': page.depth,
        'links_count': len(page.links)
    })

with open('scraped_data.json', 'w') as f:
    json.dump(pages_dict, f, indent=2)
```

### Example 3: Filter by Depth

```python
from src.scraper.web_scraper import WebScraper

scraper = WebScraper(max_depth=3, max_pages=100)
pages = scraper.scrape_website("https://example.com")

# Get only top-level pages
top_level_pages = [p for p in pages if p.depth == 0]

# Get only second-level pages
second_level_pages = [p for p in pages if p.depth == 1]

print(f"Top level: {len(top_level_pages)}")
print(f"Second level: {len(second_level_pages)}")
```

## Troubleshooting

### Issue: Too Slow

**Solution:**
- Reduce `delay` (but not below 0.5s)
- Reduce `max_pages`
- Reduce `max_depth`

### Issue: Timeouts

**Solution:**
- Increase `timeout` parameter
- Check your internet connection
- The website might be slow or blocking

### Issue: No Content Extracted

**Solution:**
- Website might be JavaScript-heavy (not supported)
- Check if website allows scraping (robots.txt)
- Try with a different user agent

### Issue: Too Many Pages

**Solution:**
- Reduce `max_depth`
- Reduce `max_pages`
- Website might have many pages (set appropriate limits)

## Testing

Run the module directly to test:

```bash
python -m src.scraper.web_scraper
```

This will run a test scrape on example.com and display results.

## Dependencies

- `requests`: HTTP library
- `beautifulsoup4`: HTML parsing
- `lxml`: Fast HTML parser (optional but recommended)
- `validators`: URL validation

## Contributing

When modifying this module:
1. Maintain backward compatibility
2. Add tests for new features
3. Update this documentation
4. Follow PEP 8 style guidelines

## License

Part of the RAG Website Scraper POC project.

## See Also

- [Main README](../../README.md)
- [Database Module](../database/README.md)
- [URL Validator](../utils/url_validator.py)
