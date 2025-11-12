"""
RAG System - Streamlit Frontend Application

This is the main application file that provides a user-friendly interface
for the RAG (Retrieval-Augmented Generation) system.

Features:
- Input website URL
- Scrape website and subpages
- Store content in vector database
- View scraping progress and results
- Search stored content
- Manage stored websites
"""

import streamlit as st
import yaml
from pathlib import Path
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper.web_scraper import WebScraper
from src.database.vector_db import VectorDatabase
from src.utils.url_validator import URLValidator


# Page configuration
st.set_page_config(
    page_title="RAG Website Scraper",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / "config" / "config.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return None


@st.cache_resource
def initialize_database(config):
    """Initialize the vector database."""
    db_config = config.get('database', {})
    embedding_config = config.get('embedding', {})

    return VectorDatabase(
        db_type=db_config.get('type', 'chromadb'),
        chroma_path=db_config.get('chroma_path', './data/chroma'),
        sqlite_path=db_config.get('sqlite_path', './data/scraped_data.db'),
        collection_name=db_config.get('collection_name', 'website_content'),
        embedding_model=embedding_config.get('model_name', 'all-MiniLM-L6-v2')
    )


def scrape_and_store_website(url: str, config: dict, db: VectorDatabase):
    """
    Scrape a website and store content in the database.

    Args:
        url (str): Website URL to scrape
        config (dict): Configuration dictionary
        db (VectorDatabase): Database instance
    """
    scraper_config = config.get('scraper', {})

    # Initialize scraper
    scraper = WebScraper(
        max_depth=scraper_config.get('max_depth', 3),
        max_pages=scraper_config.get('max_pages', 50),
        timeout=scraper_config.get('timeout', 10),
        delay=scraper_config.get('delay', 1),
        user_agent=scraper_config.get('user_agent', 'Mozilla/5.0')
    )

    # Create progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Start scraping
        status_text.text("🔍 Starting website scrape...")
        progress_bar.progress(10)

        scraped_pages = scraper.scrape_website(url)

        if not scraped_pages:
            st.error("No pages were scraped. Please check the URL and try again.")
            return None

        progress_bar.progress(50)
        status_text.text(f"✅ Scraped {len(scraped_pages)} pages. Storing in database...")

        # Store in database
        urls = [page.url for page in scraped_pages]
        titles = [page.title for page in scraped_pages]
        contents = [page.content for page in scraped_pages]
        metadatas = [page.metadata for page in scraped_pages]

        success = db.add_documents(
            urls=urls,
            titles=titles,
            contents=contents,
            metadatas=metadatas,
            website_url=url
        )

        progress_bar.progress(100)

        if success:
            status_text.text("✅ Successfully stored all pages in database!")
            return scraper.get_scrape_summary()
        else:
            st.error("Failed to store pages in database.")
            return None

    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None


def main():
    """Main application function."""

    # Load configuration
    config = load_config()
    if not config:
        st.error("Failed to load configuration. Please check config/config.yaml")
        return

    # Initialize database
    try:
        db = initialize_database(config)
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        return

    # Initialize URL validator
    url_validator = URLValidator()

    # Sidebar
    with st.sidebar:
        st.title("🌐 RAG System")
        st.markdown("---")

        # Database stats
        st.subheader("📊 Database Stats")
        stats = db.get_stats()
        st.metric("Database Type", stats.get('database_type', 'Unknown'))
        st.metric("Total Documents", stats.get('total_documents', 0))

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["🏠 Scrape Website", "🔍 Search Content", "📚 View All Documents", "⚙️ Settings"],
            label_visibility="collapsed"
        )

    # Main content area
    st.title("RAG Website Scraper POC")
    st.markdown("### Extract and store website content for RAG applications")

    # Page: Scrape Website
    if page == "🏠 Scrape Website":
        st.header("🏠 Scrape Website")

        col1, col2 = st.columns([3, 1])

        with col1:
            website_url = st.text_input(
                "Enter Website URL",
                placeholder="https://example.com",
                help="Enter the URL of the website you want to scrape"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            scrape_button = st.button("🚀 Start Scraping", type="primary", use_container_width=True)

        if scrape_button:
            if not website_url:
                st.warning("Please enter a website URL")
            else:
                # Validate URL
                normalized_url = url_validator.normalize_url(website_url)

                if not normalized_url:
                    st.error("Invalid URL. Please enter a valid website URL.")
                else:
                    st.info(f"Scraping: {normalized_url}")

                    # Scrape and store
                    summary = scrape_and_store_website(normalized_url, config, db)

                    if summary:
                        st.success("🎉 Scraping completed successfully!")

                        # Display summary
                        st.subheader("📊 Scraping Summary")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Pages Scraped", summary.get('total_pages', 0))

                        with col2:
                            st.metric("Max Depth", summary.get('max_depth_reached', 0))

                        with col3:
                            st.metric("Total Content (chars)", summary.get('total_content_length', 0))

        # Instructions
        with st.expander("ℹ️ How it works"):
            st.markdown("""
            **This tool will:**
            1. Validate and normalize your URL
            2. Scrape the main page and all linked subpages (within the same domain)
            3. Extract text content, titles, and metadata
            4. Store everything in a vector database for efficient retrieval
            5. Enable semantic search across all scraped content

            **Configuration:**
            - Maximum depth: {max_depth} levels
            - Maximum pages: {max_pages} pages
            - Delay between requests: {delay}s (to be polite!)

            **Note:** The scraper only follows links within the same domain to avoid
            crawling the entire internet!
            """.format(
                max_depth=config.get('scraper', {}).get('max_depth', 3),
                max_pages=config.get('scraper', {}).get('max_pages', 50),
                delay=config.get('scraper', {}).get('delay', 1)
            ))

    # Page: Search Content
    elif page == "🔍 Search Content":
        st.header("🔍 Search Content")

        search_query = st.text_input(
            "Enter search query",
            placeholder="Search for content...",
            help="Enter keywords to search across all scraped content"
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            website_filter = st.text_input(
                "Filter by website (optional)",
                placeholder="https://example.com",
                help="Only search within a specific website"
            )

        with col2:
            num_results = st.number_input(
                "Number of results",
                min_value=1,
                max_value=20,
                value=5
            )

        if st.button("🔍 Search", type="primary"):
            if not search_query:
                st.warning("Please enter a search query")
            else:
                results = db.search(
                    query=search_query,
                    n_results=num_results,
                    website_url=website_filter if website_filter else None
                )

                if not results:
                    st.info("No results found")
                else:
                    st.success(f"Found {len(results)} results")

                    for i, result in enumerate(results, 1):
                        with st.expander(f"Result {i}: {result['metadata'].get('title', 'Untitled')}"):
                            st.markdown(f"**URL:** {result['metadata'].get('url', 'N/A')}")
                            st.markdown(f"**Content Preview:**")
                            st.text(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])

                            if 'distance' in result and result['distance'] is not None:
                                st.markdown(f"**Similarity Score:** {1 - result['distance']:.4f}")

    # Page: View All Documents
    elif page == "📚 View All Documents":
        st.header("📚 All Documents")

        website_filter = st.text_input(
            "Filter by website (optional)",
            placeholder="https://example.com",
            help="Filter documents by website URL"
        )

        if st.button("📥 Load Documents"):
            documents = db.get_all_documents(
                website_url=website_filter if website_filter else None
            )

            if not documents:
                st.info("No documents found")
            else:
                st.success(f"Found {len(documents)} documents")

                # Display in a table format
                for i, doc in enumerate(documents, 1):
                    with st.expander(f"{i}. {doc['metadata'].get('title', 'Untitled')}"):
                        st.markdown(f"**URL:** {doc['metadata'].get('url', 'N/A')}")
                        st.markdown(f"**Timestamp:** {doc['metadata'].get('timestamp', 'N/A')}")
                        st.markdown(f"**Content Length:** {len(doc['content'])} characters")
                        st.markdown("---")
                        st.text_area(
                            "Content",
                            value=doc['content'][:1000] + "..." if len(doc['content']) > 1000 else doc['content'],
                            height=200,
                            key=f"doc_{i}"
                        )

    # Page: Settings
    elif page == "⚙️ Settings":
        st.header("⚙️ Settings")

        st.subheader("Database Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Database Type:** {config.get('database', {}).get('type', 'chromadb')}")
            st.info(f"**Collection:** {config.get('database', {}).get('collection_name', 'website_content')}")

        with col2:
            st.info(f"**Embedding Model:** {config.get('embedding', {}).get('model_name', 'all-MiniLM-L6-v2')}")
            st.info(f"**Chunk Size:** {config.get('embedding', {}).get('chunk_size', 512)}")

        st.markdown("---")

        st.subheader("Scraper Configuration")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"**Max Depth:** {config.get('scraper', {}).get('max_depth', 3)}")

        with col2:
            st.info(f"**Max Pages:** {config.get('scraper', {}).get('max_pages', 50)}")

        with col3:
            st.info(f"**Delay:** {config.get('scraper', {}).get('delay', 1)}s")

        st.markdown("---")

        st.subheader("🗑️ Danger Zone")

        st.warning("**Warning:** The following action cannot be undone!")

        website_to_clear = st.text_input(
            "Website URL to clear (leave empty to clear all)",
            placeholder="https://example.com"
        )

        if st.button("🗑️ Clear Database", type="secondary"):
            confirm = st.checkbox("I understand this will delete data permanently")

            if confirm:
                db.clear_collection(website_url=website_to_clear if website_to_clear else None)
                st.success("Database cleared successfully!")
                st.rerun()
            else:
                st.info("Please confirm to proceed with deletion")

        st.markdown("---")

        st.subheader("ℹ️ About")
        st.markdown("""
        **RAG Website Scraper POC**

        Version: 1.0.0

        This is a Proof of Concept (POC) for a RAG (Retrieval-Augmented Generation) system
        that scrapes websites and stores content in a vector database for efficient retrieval.

        **Tech Stack:**
        - Frontend: Streamlit
        - Scraping: BeautifulSoup4 + Requests
        - Database: ChromaDB (with SQLite fallback)
        - Embeddings: Sentence Transformers

        **Next Steps:**
        - Integrate Google Gemini API for RAG
        - Add question-answering capabilities
        - Implement chat interface
        """)


if __name__ == "__main__":
    main()
