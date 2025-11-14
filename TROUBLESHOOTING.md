# Troubleshooting Guide

## ChromaDB Metadata Type Errors

### Problem
You may encounter errors like:
```
ERROR: Expected metadata value to be a str, int, float or bool, got [...] which is a <class 'list'>
```

### Solutions (in order of recommendation)

#### Solution 1: Use the Automatic Fallback (Default)
The system now automatically falls back to SQLite if ChromaDB fails. You don't need to do anything - just run the application and it will handle the fallback automatically.

**How it works:**
- System tries to use ChromaDB first
- If ChromaDB fails due to metadata issues, it automatically switches to SQLite
- Your data is still saved, just in SQLite instead
- You'll see a warning message in the logs

#### Solution 2: Switch to SQLite Directly (Recommended if having persistent issues)

If you want to skip ChromaDB entirely and use SQLite from the start:

1. Edit `config/config.yaml`
2. Change the database type:
```yaml
database:
  type: "sqlite"  # Changed from "chromadb" to "sqlite"
  sqlite_path: "./data/scraped_data.db"
```
3. Restart the Streamlit application

**Benefits of SQLite:**
- ✅ No metadata type issues
- ✅ Simpler and more reliable
- ✅ No external dependencies
- ✅ Fast for small to medium datasets
- ✅ Works out of the box

**Limitations:**
- ❌ No semantic/similarity search (uses text matching instead)
- ❌ Slower for very large datasets
- ❌ No vector embeddings

#### Solution 3: Reinstall ChromaDB

If you want to keep using ChromaDB with semantic search:

```bash
# Uninstall ChromaDB
pip uninstall chromadb

# Clear cache
pip cache purge

# Reinstall with specific version
pip install chromadb==0.4.22

# Or try latest version
pip install chromadb --upgrade
```

#### Solution 4: Clear ChromaDB Data

Sometimes corrupted data causes issues:

```bash
# Stop the Streamlit application
# Then delete the ChromaDB directory
rm -rf data/chroma/

# Restart the application - it will create a fresh database
streamlit run app.py
```

#### Solution 5: Use SQLite with Manual Embeddings

If you want both reliability AND semantic search, you can use SQLite with a simpler embedding approach. This requires code modification but provides the best of both worlds.

## Other Common Issues

### Issue: "Module 'chromadb' has no attribute..."

**Solution:**
```bash
pip install chromadb --upgrade
# Or switch to SQLite (see Solution 2 above)
```

### Issue: "PermissionError: [Errno 13] Permission denied"

**Solution:**
```bash
# Make sure data directory has proper permissions
chmod -R 755 data/

# Or delete and recreate
rm -rf data/
mkdir data
```

### Issue: "Database is locked"

**Solution:**
```bash
# Close all instances of the application
# Delete the lock file
rm data/scraped_data.db-journal

# Restart application
```

### Issue: Scraping is very slow

**Solutions:**
1. Reduce `max_pages` in `config/config.yaml`
2. Reduce `max_depth`
3. Decrease `delay` (but not below 0.5s - be polite!)
4. Check your internet connection

### Issue: Out of memory

**Solutions:**
1. Reduce `max_pages` to scrape fewer pages
2. Switch to SQLite (uses less memory)
3. Clear old data regularly

## Testing Your Setup

### Test 1: Verify Database Type

```python
from src.database.vector_db import VectorDatabase

db = VectorDatabase()
stats = db.get_stats()
print(f"Database type: {stats['database_type']}")
```

### Test 2: Test with Simple Data

```python
from src.database.vector_db import VectorDatabase

db = VectorDatabase(db_type="chromadb")  # or "sqlite"

# Try adding simple data
success = db.add_documents(
    urls=["https://test.com"],
    titles=["Test Page"],
    contents=["This is test content"],
    website_url="https://test.com"
)

print(f"Success: {success}")
```

### Test 3: Check ChromaDB Installation

```bash
python -c "import chromadb; print(chromadb.__version__)"
```

## Getting Help

If none of these solutions work:

1. Check the logs in the terminal for detailed error messages
2. Try running with SQLite (most reliable option)
3. Check GitHub issues: https://github.com/chroma-core/chroma/issues
4. Open an issue in this repository with:
   - Full error message
   - Your Python version
   - Your ChromaDB version
   - Your operating system

## Recommended Configuration for Production

For the most reliable setup, use SQLite:

```yaml
# config/config.yaml
database:
  type: "sqlite"
  sqlite_path: "./data/scraped_data.db"

scraper:
  max_depth: 2
  max_pages: 100
  delay: 1
```

This configuration:
- ✅ Always works (no metadata issues)
- ✅ Fast and reliable
- ✅ Suitable for most use cases
- ✅ Easy to backup (single .db file)

## FAQ

**Q: Will I lose my data if I switch from ChromaDB to SQLite?**
A: Yes, they use different storage formats. You'll need to re-scrape websites if you switch.

**Q: Can I use both ChromaDB and SQLite?**
A: Not simultaneously, but you can switch between them by changing the config file.

**Q: Which is better - ChromaDB or SQLite?**
A:
- ChromaDB: Better for semantic search, finding similar content
- SQLite: More reliable, simpler, works everywhere

**Q: Do I need to install anything extra for SQLite?**
A: No, SQLite is built into Python. It works out of the box.

**Q: Will the automatic fallback work every time?**
A: The fallback triggers when ChromaDB fails. If both fail, check the error logs.
