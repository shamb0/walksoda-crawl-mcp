"""
Search tools facade.

Re-exports from core/ modules for backward compatibility.
"""

from ..core.search import search_google, batch_search_google, get_search_genres, multi_site_search
from ..core.search_crawl import search_and_crawl

__all__ = [
    'search_google', 'batch_search_google', 'get_search_genres',
    'search_and_crawl', 'multi_site_search',
]
