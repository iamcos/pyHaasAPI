"""
Centralized Backtest Fetcher

This module provides a unified interface for fetching backtest data from HaasOnline API
with proper pagination, error handling, and retry logic.

Eliminates scattered GetBacktestResultRequest usage across 20+ files and provides
consistent pagination handling throughout the codebase.
"""

import time
import logging
from dataclasses import dataclass
from typing import List, Optional, Generator, Union, Dict, Any
from contextlib import contextmanager

from pyHaasAPI.api import SyncExecutor, Authenticated
from pyHaasAPI.model import GetBacktestResultRequest, LabBacktestResult
from pyHaasAPI import api

logger = logging.getLogger(__name__)


@dataclass
class BacktestFetchConfig:
    """Configuration for backtest fetching operations"""
    page_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    max_pages: Optional[int] = None
    timeout: float = 30.0
    sort_by: Optional[str] = None
    filter_criteria: Optional[Dict[str, Any]] = None


class BacktestFetcher:
    """
    Centralized backtest fetcher with proper pagination and error handling.
    
    Replaces scattered GetBacktestResultRequest usage across the codebase
    with a unified, maintainable solution.
    """
    
    def __init__(self, executor: SyncExecutor[Authenticated], config: Optional[BacktestFetchConfig] = None):
        """
        Initialize the backtest fetcher.
        
        Args:
            executor: Authenticated API executor
            config: Optional configuration for fetching behavior
        """
        self.executor = executor
        self.config = config or BacktestFetchConfig()
        
    def fetch_single_page(
        self, 
        lab_id: str, 
        page_id: int = 0, 
        page_size: Optional[int] = None
    ) -> Optional[Any]:
        """
        Fetch a single page of backtest results.
        
        Args:
            lab_id: Lab identifier
            page_id: Page number (0-based)
            page_size: Override default page size
            
        Returns:
            BacktestResult object or None if failed
        """
        page_size = page_size or self.config.page_size
        
        for attempt in range(self.config.max_retries):
            try:
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=page_id,
                    page_lenght=page_size
                )
                
                logger.debug(f"Fetching page {page_id} for lab {lab_id} (attempt {attempt + 1})")
                response = api.get_backtest_result(self.executor, request)
                
                if response:
                    logger.debug(f"Successfully fetched page {page_id} with {len(response.items) if hasattr(response, 'items') else 0} items")
                    return response
                else:
                    logger.warning(f"Empty response for page {page_id} (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"Error fetching page {page_id} (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise
                    
        return None
    
    def fetch_backtests(
        self, 
        lab_id: str, 
        max_pages: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> List[Any]:
        """
        Fetch all backtest results for a lab with proper pagination.
        
        Args:
            lab_id: Lab identifier
            max_pages: Maximum number of pages to fetch (None for all)
            page_size: Override default page size
            
        Returns:
            List of all backtest items
        """
        max_pages = max_pages or self.config.max_pages
        page_size = page_size or self.config.page_size
        
        all_backtests = []
        page_id = 0
        
        logger.info(f"Starting backtest fetch for lab {lab_id} (page_size={page_size}, max_pages={max_pages})")
        
        while True:
            if max_pages and page_id >= max_pages:
                logger.info(f"Reached max pages limit ({max_pages})")
                break
                
            response = self.fetch_single_page(lab_id, page_id, page_size)
            
            if not response or not hasattr(response, 'items'):
                logger.info(f"No more data at page {page_id}")
                break
                
            items = response.items
            if not items:
                logger.info(f"Empty page {page_id}, stopping")
                break
                
            all_backtests.extend(items)
            logger.debug(f"Page {page_id}: {len(items)} items (total: {len(all_backtests)})")
            
            # Check if we've reached the end
            if len(items) < page_size:
                logger.info(f"Last page reached (got {len(items)} < {page_size})")
                break
                
            page_id += 1
            
        logger.info(f"Completed backtest fetch for lab {lab_id}: {len(all_backtests)} total backtests")
        return all_backtests
    
    def fetch_all_backtests(self, lab_id: str) -> List[Any]:
        """
        Fetch all backtest results for a lab (convenience method).
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            List of all backtest items
        """
        return self.fetch_backtests(lab_id, max_pages=None)
    
    def fetch_top_backtests(
        self, 
        lab_id: str, 
        top_count: int = 10,
        page_size: Optional[int] = None
    ) -> List[Any]:
        """
        Fetch top N backtest results for a lab.
        
        Args:
            lab_id: Lab identifier
            top_count: Number of top backtests to fetch
            page_size: Override default page size
            
        Returns:
            List of top backtest items
        """
        page_size = page_size or self.config.page_size
        
        # Calculate how many pages we need
        pages_needed = (top_count + page_size - 1) // page_size
        
        logger.info(f"Fetching top {top_count} backtests for lab {lab_id} (need {pages_needed} pages)")
        
        all_backtests = self.fetch_backtests(lab_id, max_pages=pages_needed, page_size=page_size)
        
        # Return only the requested number
        return all_backtests[:top_count]
    
    def fetch_backtests_generator(
        self, 
        lab_id: str, 
        page_size: Optional[int] = None
    ) -> Generator[List[Any], None, None]:
        """
        Generator that yields backtest results page by page.
        
        Args:
            lab_id: Lab identifier
            page_size: Override default page size
            
        Yields:
            List of backtest items for each page
        """
        page_size = page_size or self.config.page_size
        page_id = 0
        
        while True:
            response = self.fetch_single_page(lab_id, page_id, page_size)
            
            if not response or not hasattr(response, 'items') or not response.items:
                break
                
            yield response.items
            page_id += 1
            
            # Stop if we got fewer items than requested (last page)
            if len(response.items) < page_size:
                break


# Convenience functions for common use cases

def fetch_lab_backtests(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    config: Optional[BacktestFetchConfig] = None
) -> List[Any]:
    """
    Convenience function to fetch all backtests for a lab.
    
    Args:
        executor: Authenticated API executor
        lab_id: Lab identifier
        config: Optional fetch configuration
        
    Returns:
        List of all backtest items
    """
    fetcher = BacktestFetcher(executor, config)
    return fetcher.fetch_all_backtests(lab_id)


def fetch_top_performers(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    top_count: int = 10,
    config: Optional[BacktestFetchConfig] = None
) -> List[Any]:
    """
    Convenience function to fetch top performing backtests.
    
    Args:
        executor: Authenticated API executor
        lab_id: Lab identifier
        top_count: Number of top backtests to fetch
        config: Optional fetch configuration
        
    Returns:
        List of top backtest items
    """
    fetcher = BacktestFetcher(executor, config)
    return fetcher.fetch_top_backtests(lab_id, top_count)


def fetch_all_lab_backtests(
    executor: SyncExecutor[Authenticated], 
    lab_id: str,
    page_size: int = 100,
    max_retries: int = 3
) -> List[Any]:
    """
    Convenience function with common defaults for fetching all lab backtests.
    
    Args:
        executor: Authenticated API executor
        lab_id: Lab identifier
        page_size: Page size for pagination
        max_retries: Maximum retry attempts
        
    Returns:
        List of all backtest items
    """
    config = BacktestFetchConfig(page_size=page_size, max_retries=max_retries)
    return fetch_lab_backtests(executor, lab_id, config)


@contextmanager
def backtest_fetcher(executor: SyncExecutor[Authenticated], config: Optional[BacktestFetchConfig] = None):
    """
    Context manager for backtest fetcher with automatic cleanup.
    
    Args:
        executor: Authenticated API executor
        config: Optional fetch configuration
        
    Yields:
        BacktestFetcher instance
    """
    fetcher = BacktestFetcher(executor, config)
    try:
        yield fetcher
    finally:
        # Cleanup if needed
        pass
