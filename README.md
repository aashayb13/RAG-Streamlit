# RAG Website Scraper POC

A comprehensive Proof of Concept (POC) for a Retrieval-Augmented Generation (RAG) system that intelligently scrapes websites and stores content in a vector database for efficient retrieval and future AI-powered question answering.

## Overview

This project provides a complete end-to-end solution for:
- **Web Scraping**: Extract content from any website including all subpages
- **Vector Storage**: Store content in ChromaDB for semantic search
- **User Interface**: Easy-to-use Streamlit frontend
- **Modular Architecture**: Clean, industry-standard code structure

## Features

### Current Features (Phase 1)
- ✅ Streamlit frontend for URL input
- ✅ Intelligent web scraper with subpage discovery
- ✅ Vector database storage (ChromaDB with SQLite fallback)
- ✅ Semantic search across scraped content
- ✅ Document management and viewing
- ✅ Progress tracking and statistics
- ✅ Configurable scraping parameters

### Planned Features (Phase 2)
- 🔄 Google Gemini API integration
- 🔄 RAG-based question answering
- 🔄 Chat interface for querying website content
- 🔄 Advanced content chunking strategies
- 🔄 Multi-website comparison

## Project Structure

```
RAG-Streamlit/
├── README.md                    # Main project documentation
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── app.py                       # Main Streamlit application
├── config/
│   └── config.yaml             # Configuration settings
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── web_scraper.py      # Web scraping logic
│   │   └── README.md           # Scraper documentation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── vector_db.py        # Vector database operations
│   │   └── README.md           # Database documentation
│   └── utils/
│       ├── __init__.py
│       └── url_validator.py    # URL validation utilities
└── data/                        # Database storage (auto-created)
    ├── chroma/                  # ChromaDB files
    └── scraped_data.db         # SQLite fallback
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd RAG-Streamlit
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**💡 Quick Tip:** If you encounter ChromaDB issues, the system will automatically fallback to SQLite. Or you can switch to SQLite directly by editing `config/config.yaml` and changing `type: "chromadb"` to `type: "sqlite"` - SQLite works perfectly and requires no additional setup!

This will install:
- **streamlit**: Web application framework
- **beautifulsoup4**: HTML parsing
- **requests**: HTTP library
- **chromadb**: Vector database
- **sentence-transformers**: Text embeddings
- **pandas**: Data manipulation
- **validators**: URL validation
- And other supporting libraries

## Usage

### Running the Application

1. Make sure your virtual environment is activated

2. Run the Streamlit app:
```bash
streamlit run app.py
```

3. The application will open in your default browser at `http://localhost:8501`

### Using the Interface

#### 1. Scrape a Website

1. Navigate to **🏠 Scrape Website**
2. Enter a website URL (e.g., `https://example.com`)
3. Click **🚀 Start Scraping**
4. Wait for the scraper to complete
5. View the scraping summary

#### 2. Search Content

1. Navigate to **🔍 Search Content**
2. Enter a search query
3. Optionally filter by website URL
4. Set the number of results
5. Click **🔍 Search**
6. Browse the results

#### 3. View All Documents

1. Navigate to **📚 View All Documents**
2. Optionally filter by website
3. Click **📥 Load Documents**
4. Expand documents to view content

#### 4. Configure Settings

1. Navigate to **⚙️ Settings**
2. View current configuration
3. Clear database if needed (use with caution!)

## Configuration

Edit `config/config.yaml` to customize behavior:

```yaml
# Scraper Settings
scraper:
  max_depth: 3        # How deep to crawl (levels from main page)
  max_pages: 50       # Maximum pages to scrape per website
  timeout: 10         # Request timeout in seconds
  delay: 1            # Delay between requests (be polite!)

# Database Settings
database:
  type: "chromadb"    # Options: "chromadb" or "sqlite"
  chroma_path: "./data/chroma"
  collection_name: "website_content"

# Embedding Settings
embedding:
  model_name: "all-MiniLM-L6-v2"  # Sentence transformer model
  chunk_size: 512
```

## Module Documentation

### Web Scraper Module

Located in `src/scraper/web_scraper.py`

**Key Features:**
- Breadth-first crawling of websites
- Automatic subpage discovery
- Same-domain restriction (prevents crawling entire internet)
- Polite crawling with configurable delays
- Comprehensive error handling
- Extracts: title, content, metadata, links

**Usage Example:**
```python
from src.scraper.web_scraper import WebScraper

scraper = WebScraper(max_depth=3, max_pages=50)
pages = scraper.scrape_website("https://example.com")

for page in pages:
    print(f"{page.title}: {len(page.content)} chars")
```

See [src/scraper/README.md](src/scraper/README.md) for detailed documentation.

### Vector Database Module

Located in `src/database/vector_db.py`

**Key Features:**
- ChromaDB integration for vector storage
- SQLite fallback option
- Automatic embedding generation
- Semantic search capabilities
- Document management (add, search, delete)
- Website-based filtering

**Usage Example:**
```python
from src.database.vector_db import VectorDatabase

db = VectorDatabase(db_type="chromadb")
db.add_documents(
    urls=["https://example.com"],
    titles=["Example"],
    contents=["Content here..."]
)

results = db.search("search query", n_results=5)
```

See [src/database/README.md](src/database/README.md) for detailed documentation.

### URL Validator Utility

Located in `src/utils/url_validator.py`

**Key Features:**
- URL format validation
- URL normalization
- Domain extraction
- Relative to absolute URL conversion
- Same-domain checking

**Usage Example:**
```python
from src.utils.url_validator import URLValidator

validator = URLValidator()
normalized = validator.normalize_url("example.com")
# Returns: "https://example.com"
```

## Technical Details

### Web Scraping Process

1. **URL Validation**: Normalize and validate the input URL
2. **Initial Request**: Fetch the main page
3. **Content Extraction**: Parse HTML and extract text, metadata
4. **Link Discovery**: Find all links on the page
5. **Recursive Crawling**: Follow links within same domain
6. **Depth Control**: Stop at configured depth limit
7. **Page Limit**: Stop at configured page count

### Database Storage

#### ChromaDB (Recommended)
- **Vector Embeddings**: Automatic generation using Sentence Transformers
- **Semantic Search**: Find similar content based on meaning
- **Persistent Storage**: Data saved to disk
- **Fast Retrieval**: Optimized for similarity search

#### SQLite (Fallback)
- **Traditional Database**: Relational storage
- **Text Search**: Basic keyword matching
- **Lightweight**: No external dependencies
- **Reliable**: Battle-tested database engine

### Embedding Model

**Model**: `all-MiniLM-L6-v2`
- **Size**: Small and fast
- **Quality**: Good balance of speed and accuracy
- **Dimensions**: 384
- **Use Case**: Suitable for semantic search

## Best Practices

### When Scraping
- ✅ Always check `robots.txt` before scraping
- ✅ Use appropriate delays between requests (default: 1s)
- ✅ Respect the website's terms of service
- ✅ Don't scrape copyrighted content without permission
- ✅ Start with small max_pages for testing

### Database Management
- ✅ Regularly backup your `data/` directory
- ✅ Clear old data before scraping updated versions
- ✅ Monitor database size
- ✅ Use website-specific filters when searching

### Configuration
- ✅ Adjust `max_depth` based on website structure
- ✅ Set reasonable `max_pages` limits
- ✅ Increase `delay` for slower servers
- ✅ Use SQLite for simple use cases

## Troubleshooting

**📘 For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Quick Solutions

#### ChromaDB Metadata Errors
The system has **automatic fallback to SQLite** if ChromaDB fails. You don't need to do anything!

Alternatively, switch to SQLite directly in `config/config.yaml`:
```yaml
database:
  type: "sqlite"  # Change from "chromadb" to "sqlite"
```

#### Common Issues

**1. ChromaDB Installation Fails**
```bash
# Use SQLite instead - it's more reliable
# Edit config/config.yaml and set: type: "sqlite"
```

**2. Scraper Times Out**
```yaml
scraper:
  timeout: 30  # Increase in config.yaml
```

**3. Too Many Pages Scraped**
```yaml
scraper:
  max_depth: 2
  max_pages: 20
```

**4. Memory Issues**
- Use SQLite instead of ChromaDB (lighter weight)
- Reduce max_pages
- Clear database regularly

📘 **See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete solutions**

## Development

### Running Tests

```bash
# Test individual modules
python -m src.scraper.web_scraper
python -m src.database.vector_db
python -m src.utils.url_validator
```

### Code Style

This project follows PEP 8 guidelines:
- Type hints for function signatures
- Docstrings for all modules, classes, and functions
- Clear variable names
- Modular, reusable code

## Future Enhancements

### Phase 2: RAG Integration
- [ ] Integrate Google Gemini API
- [ ] Implement question-answering system
- [ ] Add chat interface
- [ ] Context-aware responses

### Phase 3: Advanced Features
- [ ] Multi-language support
- [ ] PDF/Document scraping
- [ ] Image content extraction
- [ ] Scheduled scraping
- [ ] API endpoints

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for educational and development purposes.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the module-specific README files
- Review the inline code documentation

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Sentence Transformers](https://www.sbert.net/) - Text embeddings

---

**Version**: 1.0.0
**Status**: POC (Proof of Concept)
**Last Updated**: 2024
