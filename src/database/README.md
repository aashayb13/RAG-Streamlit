# Vector Database Module

## Overview

The Vector Database module provides a unified interface for storing and retrieving scraped website content using vector embeddings. It supports both ChromaDB (recommended) for semantic search and SQLite as a fallback option.

## Features

- **Vector Storage**: Store content with automatic embedding generation
- **Semantic Search**: Find similar content based on meaning, not just keywords
- **Dual Backend**: ChromaDB (primary) with SQLite fallback
- **Document Management**: Add, search, retrieve, and delete documents
- **Website Filtering**: Organize and filter by source website
- **Persistent Storage**: Data saved to disk for later use
- **Statistics**: Track database size and content

## Architecture

### Supported Databases

#### 1. ChromaDB (Recommended)
- **Vector embeddings** for semantic search
- **Similarity search** based on meaning
- **Fast retrieval** optimized for AI applications
- **Persistent storage** to disk

#### 2. SQLite (Fallback)
- **Traditional database** with SQL queries
- **Text search** using LIKE queries
- **Lightweight** and no dependencies
- **Reliable** and widely supported

## Usage

### Basic Usage

```python
from src.database.vector_db import VectorDatabase

# Initialize database (ChromaDB by default)
db = VectorDatabase(db_type="chromadb")

# Add documents
success = db.add_documents(
    urls=["https://example.com", "https://example.com/about"],
    titles=["Home Page", "About Us"],
    contents=["Welcome to our website...", "We are a company..."],
    website_url="https://example.com"
)

# Search for similar content
results = db.search(
    query="tell me about the company",
    n_results=5
)

# Display results
for result in results:
    print(f"Title: {result['metadata']['title']}")
    print(f"URL: {result['metadata']['url']}")
    print(f"Content: {result['content'][:200]}...")
    print()
```

### Advanced Usage

```python
from src.database.vector_db import VectorDatabase

# Custom configuration
db = VectorDatabase(
    db_type="chromadb",
    chroma_path="./my_data/chroma",
    collection_name="my_collection",
    embedding_model="all-MiniLM-L6-v2"
)

# Add documents with metadata
db.add_documents(
    urls=["https://example.com"],
    titles=["Example Page"],
    contents=["Page content..."],
    metadatas=[{
        "author": "John Doe",
        "date": "2024-01-01",
        "category": "blog"
    }],
    website_url="https://example.com"
)

# Search with website filter
results = db.search(
    query="blog posts",
    n_results=10,
    website_url="https://example.com"
)

# Get all documents
all_docs = db.get_all_documents()

# Get statistics
stats = db.get_stats()
print(f"Database type: {stats['database_type']}")
print(f"Total documents: {stats['total_documents']}")
```

## Configuration

### Initialization Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_type` | str | "chromadb" | Database type ("chromadb" or "sqlite") |
| `chroma_path` | str | "./data/chroma" | Path for ChromaDB storage |
| `sqlite_path` | str | "./data/scraped_data.db" | Path for SQLite database |
| `collection_name` | str | "website_content" | Name of the collection |
| `embedding_model` | str | "all-MiniLM-L6-v2" | Sentence transformer model |

### Embedding Models

Available sentence transformer models:

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | General purpose (default) |
| `all-mpnet-base-v2` | 768 | Medium | Better | Higher quality search |
| `all-MiniLM-L12-v2` | 384 | Medium | Good | Balanced option |

## Methods

### `__init__(...)`
Initialize the vector database.

**Parameters:**
- `db_type` (str): "chromadb" or "sqlite"
- `chroma_path` (str): Path for ChromaDB storage
- `sqlite_path` (str): Path for SQLite database
- `collection_name` (str): Collection name
- `embedding_model` (str): Embedding model name

### `add_documents(...)`
Add multiple documents to the database.

**Parameters:**
- `urls` (List[str]): List of page URLs
- `titles` (List[str]): List of page titles
- `contents` (List[str]): List of page contents
- `metadatas` (Optional[List[Dict]]): List of metadata dictionaries
- `website_url` (Optional[str]): Base website URL for grouping

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = db.add_documents(
    urls=["https://example.com/page1", "https://example.com/page2"],
    titles=["Page 1", "Page 2"],
    contents=["Content 1", "Content 2"],
    website_url="https://example.com"
)
```

### `search(...)`
Search for similar documents.

**Parameters:**
- `query` (str): Search query
- `n_results` (int): Number of results to return (default: 5)
- `website_url` (Optional[str]): Filter by website URL

**Returns:**
- `List[Dict]`: List of search results with content and metadata

**Example:**
```python
results = db.search(
    query="machine learning",
    n_results=10,
    website_url="https://example.com"
)

for result in results:
    print(result['metadata']['title'])
    print(result['content'])
    if 'distance' in result:
        print(f"Similarity: {1 - result['distance']}")
```

### `get_all_documents(...)`
Get all documents, optionally filtered by website.

**Parameters:**
- `website_url` (Optional[str]): Filter by website URL

**Returns:**
- `List[Dict]`: List of all documents

**Example:**
```python
# Get all documents
all_docs = db.get_all_documents()

# Get documents from specific website
site_docs = db.get_all_documents(website_url="https://example.com")
```

### `clear_collection(...)`
Clear the collection or specific website documents.

**Parameters:**
- `website_url` (Optional[str]): If provided, only delete this website's documents

**Example:**
```python
# Clear specific website
db.clear_collection(website_url="https://example.com")

# Clear entire database (use with caution!)
db.clear_collection()
```

### `get_stats()`
Get database statistics.

**Returns:**
- `Dict`: Statistics about the database

**Example:**
```python
stats = db.get_stats()
print(f"Type: {stats['database_type']}")
print(f"Documents: {stats['total_documents']}")
if 'embedding_model' in stats:
    print(f"Model: {stats['embedding_model']}")
```

### `close()`
Close database connections.

**Example:**
```python
db.close()
```

## How It Works

### ChromaDB Flow

```
1. Document Input
   ↓
2. Text Preprocessing
   ↓
3. Embedding Generation
   (using Sentence Transformers)
   ↓
4. Store Vector + Metadata
   ↓
5. Save to Disk
```

### Search Flow

```
1. Query Input
   ↓
2. Query Embedding
   (using same model)
   ↓
3. Similarity Search
   (cosine similarity)
   ↓
4. Return Top Results
   (with distances)
```

### SQLite Flow

```
1. Document Input
   ↓
2. Store as Text
   ↓
3. Create Indexes
   ↓
4. Save to Database

Search:
1. Query Input
   ↓
2. Text Matching (LIKE)
   ↓
3. Return Results
```

## Data Structure

### ChromaDB Document Format

```python
{
    'id': 'url_encoded_id',
    'document': 'Title\n\nContent',
    'metadata': {
        'url': 'https://example.com',
        'title': 'Page Title',
        'website_url': 'https://example.com',
        'timestamp': '2024-01-01T12:00:00',
        # ... additional metadata
    }
}
```

### SQLite Schema

```sql
CREATE TABLE scraped_content (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    metadata TEXT,  -- JSON string
    timestamp TEXT,
    website_url TEXT
);

-- Indexes
CREATE INDEX idx_url ON scraped_content(url);
CREATE INDEX idx_website_url ON scraped_content(website_url);
```

## Examples

### Example 1: Full Workflow

```python
from src.database.vector_db import VectorDatabase
from src.scraper.web_scraper import WebScraper

# Scrape website
scraper = WebScraper(max_depth=2, max_pages=20)
pages = scraper.scrape_website("https://example.com")

# Store in database
db = VectorDatabase(db_type="chromadb")

urls = [page.url for page in pages]
titles = [page.title for page in pages]
contents = [page.content for page in pages]
metadatas = [page.metadata for page in pages]

db.add_documents(
    urls=urls,
    titles=titles,
    contents=contents,
    metadatas=metadatas,
    website_url="https://example.com"
)

# Search
results = db.search("pricing information", n_results=5)

for result in results:
    print(f"Found: {result['metadata']['title']}")
```

### Example 2: Multiple Websites

```python
from src.database.vector_db import VectorDatabase

db = VectorDatabase()

# Add documents from multiple websites
db.add_documents(
    urls=["https://site1.com/page"],
    titles=["Site 1 Page"],
    contents=["Content from site 1"],
    website_url="https://site1.com"
)

db.add_documents(
    urls=["https://site2.com/page"],
    titles=["Site 2 Page"],
    contents=["Content from site 2"],
    website_url="https://site2.com"
)

# Search across all sites
all_results = db.search("technology", n_results=10)

# Search within specific site
site1_results = db.search(
    "technology",
    n_results=10,
    website_url="https://site1.com"
)
```

### Example 3: Using SQLite

```python
from src.database.vector_db import VectorDatabase

# Use SQLite instead of ChromaDB
db = VectorDatabase(
    db_type="sqlite",
    sqlite_path="./my_database.db"
)

# Same API works for both!
db.add_documents(
    urls=["https://example.com"],
    titles=["Example"],
    contents=["Content..."]
)

results = db.search("example")
```

## Performance

### ChromaDB
- **Insertion**: ~100-500 docs/second (depends on content length)
- **Search**: ~1-10ms for small collections (<10k docs)
- **Storage**: ~1-2KB per document (including embeddings)

### SQLite
- **Insertion**: ~1000+ docs/second
- **Search**: ~10-100ms (depends on content length and query)
- **Storage**: ~0.5-1KB per document (text only)

## Best Practices

### When to Use ChromaDB
- Need semantic/similarity search
- Working with large collections (>1000 docs)
- Want to find conceptually related content
- Building RAG applications

### When to Use SQLite
- Simple keyword search is sufficient
- Small collections (<1000 docs)
- Want minimal dependencies
- Need reliable, proven technology

### Optimization Tips
1. **Batch Inserts**: Add multiple documents at once
2. **Appropriate Model**: Choose embedding model based on needs
3. **Regular Cleanup**: Remove old/outdated content
4. **Website Filtering**: Use website_url for organization
5. **Backup Data**: Regularly backup the data directory

## Troubleshooting

### Issue: ChromaDB Installation Fails

**Solution:**
```python
# Use SQLite instead
db = VectorDatabase(db_type="sqlite")
```

### Issue: Search Returns No Results

**Possible Causes:**
- No documents in database
- Query too specific
- Wrong website_url filter

**Solution:**
```python
# Check stats
stats = db.get_stats()
print(f"Total docs: {stats['total_documents']}")

# Try broader query
results = db.search("general topic", n_results=10)

# Remove website filter
results = db.search("query", website_url=None)
```

### Issue: Slow Search

**Solution:**
- Reduce `n_results`
- Use smaller embedding model
- Consider SQLite for simple text search
- Add website_url filter to narrow search

### Issue: Memory Usage

**Solution:**
- Reduce content length before storing
- Use smaller embedding model
- Clear old data regularly
- Consider SQLite for large datasets

## Testing

Run the module directly to test:

```bash
python -m src.database.vector_db
```

This will initialize a test database and display statistics.

## Dependencies

- `chromadb`: Vector database
- `sentence-transformers`: Text embeddings
- `sqlite3`: SQLite support (built-in)

## Contributing

When modifying this module:
1. Maintain API compatibility between ChromaDB and SQLite
2. Add tests for new features
3. Update this documentation
4. Ensure backward compatibility

## License

Part of the RAG Website Scraper POC project.

## See Also

- [Main README](../../README.md)
- [Web Scraper Module](../scraper/README.md)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
