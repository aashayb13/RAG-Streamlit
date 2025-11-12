"""
Vector Database Module

This module provides functionality to store and retrieve website content
using a vector database (ChromaDB) for efficient similarity search.

Features:
- Store scraped content with embeddings
- Search for similar content
- Manage collections
- Support for both ChromaDB and SQLite fallback
"""

import os
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import sqlite3
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    A vector database wrapper for storing and retrieving website content.

    This class supports:
    - ChromaDB for vector storage and similarity search
    - SQLite as a fallback option
    - Automatic text chunking and embedding
    - Efficient retrieval of relevant content
    """

    def __init__(
        self,
        db_type: str = "chromadb",
        chroma_path: str = "./data/chroma",
        sqlite_path: str = "./data/scraped_data.db",
        collection_name: str = "website_content",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the VectorDatabase.

        Args:
            db_type (str): Type of database ("chromadb" or "sqlite")
            chroma_path (str): Path for ChromaDB storage
            sqlite_path (str): Path for SQLite database
            collection_name (str): Name of the collection
            embedding_model (str): Name of the sentence transformer model
        """
        self.db_type = db_type
        self.chroma_path = chroma_path
        self.sqlite_path = sqlite_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        self.client = None
        self.collection = None
        self.sqlite_conn = None

        # Initialize the database
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the appropriate database based on db_type."""
        if self.db_type == "chromadb":
            self._initialize_chromadb()
        elif self.db_type == "sqlite":
            self._initialize_sqlite()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.chroma_path, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Create or get collection with embedding function
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=sentence_transformer_ef,
                metadata={"description": "Website content for RAG system"}
            )

            logger.info(f"ChromaDB initialized at {self.chroma_path}")
            logger.info(f"Collection '{self.collection_name}' ready")

        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            logger.info("Falling back to SQLite...")
            self.db_type = "sqlite"
            self._initialize_sqlite()

    def _initialize_sqlite(self):
        """Initialize SQLite database as fallback."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)

            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            cursor = self.sqlite_conn.cursor()

            # Create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraped_content (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT,
                    website_url TEXT
                )
            ''')

            # Create index on URL
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON scraped_content(url)
            ''')

            # Create index on website_url
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_website_url ON scraped_content(website_url)
            ''')

            self.sqlite_conn.commit()
            logger.info(f"SQLite database initialized at {self.sqlite_path}")

        except Exception as e:
            logger.error(f"Error initializing SQLite: {str(e)}")
            raise

    def add_documents(
        self,
        urls: List[str],
        titles: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict]] = None,
        website_url: Optional[str] = None
    ) -> bool:
        """
        Add multiple documents to the database.

        Args:
            urls (List[str]): List of page URLs
            titles (List[str]): List of page titles
            contents (List[str]): List of page contents
            metadatas (Optional[List[Dict]]): List of metadata dictionaries
            website_url (Optional[str]): Base website URL for grouping

        Returns:
            bool: True if successful, False otherwise
        """
        if not urls or len(urls) != len(titles) or len(urls) != len(contents):
            logger.error("URLs, titles, and contents must have the same length")
            return False

        try:
            if self.db_type == "chromadb":
                return self._add_documents_chromadb(urls, titles, contents, metadatas, website_url)
            else:
                return self._add_documents_sqlite(urls, titles, contents, metadatas, website_url)
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """
        Sanitize metadata for ChromaDB by converting complex types to simple types.

        ChromaDB only accepts str, int, float, and bool values in metadata.
        This method converts or removes complex types like lists and dicts.

        Args:
            metadata (Dict): Original metadata dictionary

        Returns:
            Dict: Sanitized metadata with only simple types
        """
        sanitized = {}

        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                # Simple types are fine
                sanitized[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON string
                try:
                    sanitized[key] = json.dumps(value)
                except (TypeError, ValueError):
                    # If can't serialize, skip this field
                    logger.warning(f"Skipping metadata field '{key}' - cannot serialize")
                    continue
            else:
                # Try to convert to string
                try:
                    sanitized[key] = str(value)
                except:
                    logger.warning(f"Skipping metadata field '{key}' - cannot convert to string")
                    continue

        return sanitized

    def _add_documents_chromadb(
        self,
        urls: List[str],
        titles: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict]],
        website_url: Optional[str]
    ) -> bool:
        """Add documents to ChromaDB."""
        try:
            # Prepare IDs (use URL as ID, replacing special characters)
            ids = [url.replace('/', '_').replace(':', '_').replace('.', '_') for url in urls]

            # Prepare documents (combine title and content)
            documents = [f"{title}\n\n{content}" for title, content in zip(titles, contents)]

            # Prepare metadata
            if metadatas is None:
                metadatas = [{} for _ in urls]

            # Add website_url and title to metadata
            for i, (url, title) in enumerate(zip(urls, titles)):
                metadatas[i]['url'] = url
                metadatas[i]['title'] = title
                if website_url:
                    metadatas[i]['website_url'] = website_url
                metadatas[i]['timestamp'] = datetime.now().isoformat()

            # Sanitize metadata to remove complex types
            sanitized_metadatas = [self._sanitize_metadata(meta) for meta in metadatas]

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=sanitized_metadatas
            )

            logger.info(f"Added {len(urls)} documents to ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {str(e)}")
            return False

    def _add_documents_sqlite(
        self,
        urls: List[str],
        titles: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict]],
        website_url: Optional[str]
    ) -> bool:
        """Add documents to SQLite."""
        try:
            cursor = self.sqlite_conn.cursor()

            for i, (url, title, content) in enumerate(zip(urls, titles, contents)):
                # Prepare metadata
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                metadata_json = json.dumps(metadata)

                # Generate ID
                doc_id = url.replace('/', '_').replace(':', '_').replace('.', '_')

                # Insert or replace
                cursor.execute('''
                    INSERT OR REPLACE INTO scraped_content
                    (id, url, title, content, metadata, timestamp, website_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doc_id,
                    url,
                    title,
                    content,
                    metadata_json,
                    datetime.now().isoformat(),
                    website_url or ''
                ))

            self.sqlite_conn.commit()
            logger.info(f"Added {len(urls)} documents to SQLite")
            return True

        except Exception as e:
            logger.error(f"Error adding documents to SQLite: {str(e)}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        website_url: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar documents.

        Args:
            query (str): Search query
            n_results (int): Number of results to return
            website_url (Optional[str]): Filter by website URL

        Returns:
            List[Dict]: List of search results with content and metadata
        """
        try:
            if self.db_type == "chromadb":
                return self._search_chromadb(query, n_results, website_url)
            else:
                return self._search_sqlite(query, n_results, website_url)
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []

    def _search_chromadb(
        self,
        query: str,
        n_results: int,
        website_url: Optional[str]
    ) -> List[Dict]:
        """Search using ChromaDB."""
        try:
            # Prepare where clause for filtering
            where = None
            if website_url:
                where = {"website_url": website_url}

            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []

    def _search_sqlite(
        self,
        query: str,
        n_results: int,
        website_url: Optional[str]
    ) -> List[Dict]:
        """Search using SQLite (basic text matching)."""
        try:
            cursor = self.sqlite_conn.cursor()

            # Build query
            sql_query = '''
                SELECT url, title, content, metadata
                FROM scraped_content
                WHERE content LIKE ?
            '''
            params = [f'%{query}%']

            if website_url:
                sql_query += ' AND website_url = ?'
                params.append(website_url)

            sql_query += ' LIMIT ?'
            params.append(n_results)

            cursor.execute(sql_query, params)
            rows = cursor.fetchall()

            # Format results
            formatted_results = []
            for row in rows:
                url, title, content, metadata_json = row
                metadata = json.loads(metadata_json) if metadata_json else {}

                formatted_results.append({
                    'content': content,
                    'metadata': {
                        'url': url,
                        'title': title,
                        **metadata
                    }
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching SQLite: {str(e)}")
            return []

    def get_all_documents(self, website_url: Optional[str] = None) -> List[Dict]:
        """
        Get all documents, optionally filtered by website URL.

        Args:
            website_url (Optional[str]): Filter by website URL

        Returns:
            List[Dict]: List of all documents
        """
        try:
            if self.db_type == "chromadb":
                # ChromaDB doesn't have a direct "get all" method, use peek
                results = self.collection.get()
                formatted_results = []

                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}

                    # Filter by website_url if provided
                    if website_url and metadata.get('website_url') != website_url:
                        continue

                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata
                    })

                return formatted_results

            else:
                cursor = self.sqlite_conn.cursor()

                if website_url:
                    cursor.execute(
                        'SELECT url, title, content, metadata FROM scraped_content WHERE website_url = ?',
                        (website_url,)
                    )
                else:
                    cursor.execute('SELECT url, title, content, metadata FROM scraped_content')

                rows = cursor.fetchall()

                formatted_results = []
                for row in rows:
                    url, title, content, metadata_json = row
                    metadata = json.loads(metadata_json) if metadata_json else {}

                    formatted_results.append({
                        'content': content,
                        'metadata': {
                            'url': url,
                            'title': title,
                            **metadata
                        }
                    })

                return formatted_results

        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []

    def clear_collection(self, website_url: Optional[str] = None):
        """
        Clear the collection or specific website documents.

        Args:
            website_url (Optional[str]): If provided, only delete this website's documents
        """
        try:
            if self.db_type == "chromadb":
                if website_url:
                    # Delete specific documents
                    results = self.collection.get(where={"website_url": website_url})
                    if results['ids']:
                        self.collection.delete(ids=results['ids'])
                        logger.info(f"Deleted {len(results['ids'])} documents for {website_url}")
                else:
                    # Clear entire collection
                    self.client.delete_collection(self.collection_name)
                    self._initialize_chromadb()
                    logger.info("Collection cleared")
            else:
                cursor = self.sqlite_conn.cursor()
                if website_url:
                    cursor.execute('DELETE FROM scraped_content WHERE website_url = ?', (website_url,))
                else:
                    cursor.execute('DELETE FROM scraped_content')
                self.sqlite_conn.commit()
                logger.info("Database cleared")

        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")

    def get_stats(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dict: Statistics about the database
        """
        try:
            if self.db_type == "chromadb":
                count = self.collection.count()
                return {
                    'database_type': 'ChromaDB',
                    'collection_name': self.collection_name,
                    'total_documents': count,
                    'embedding_model': self.embedding_model
                }
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM scraped_content')
                count = cursor.fetchone()[0]

                return {
                    'database_type': 'SQLite',
                    'database_path': self.sqlite_path,
                    'total_documents': count
                }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}

    def close(self):
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("SQLite connection closed")


if __name__ == "__main__":
    # Test the vector database
    db = VectorDatabase(db_type="chromadb")

    print("\n" + "=" * 60)
    print("DATABASE STATS")
    print("=" * 60)

    stats = db.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
