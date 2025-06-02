# Base Scraper Module
# src/scrapers/modules/base_scraper.py

import asyncio
import aiohttp
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

@dataclass
class ContentItem:
    """Data model for scraped content items"""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: List[str] = None
    summary: Optional[str] = None
    source_name: str = ""
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc)

class BaseScraper(ABC):
    """Base class for all content scrapers"""
    
    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.source_name = source_config.get("name", "Unknown")
        self.base_url = source_config.get("base_url", "")
        self.rate_limit = source_config.get("rate_limit", 1.0)  # seconds between requests
        self.max_concurrent = source_config.get("max_concurrent", 5)
        self.timeout = source_config.get("timeout", 30)
        self.headers = source_config.get("headers", {
            "User-Agent": "Mozilla/5.0 (compatible; NicheSyndicationBot/1.0)"
        })
        
        self.logger = logging.getLogger(f"scraper.{self.source_name}")
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def rate_limit_delay(self):
        """Enforce rate limiting between requests"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
        
    async def fetch_url(self, url: str, **kwargs) -> Optional[str]:
        """Fetch content from a URL with error handling and rate limiting"""
        await self.rate_limit_delay()
        
        try:
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
            
    @abstractmethod
    async def discover_urls(self) -> List[str]:
        """Discover URLs to scrape from the source"""
        pass
        
    @abstractmethod
    async def parse_content(self, url: str, html: str) -> Optional[ContentItem]:
        """Parse content from HTML and return ContentItem"""
        pass
        
    async def scrape_single_url(self, url: str) -> Optional[ContentItem]:
        """Scrape a single URL and return ContentItem"""
        self.logger.info(f"Scraping {url}")
        
        html = await self.fetch_url(url)
        if not html:
            return None
            
        try:
            content_item = await self.parse_content(url, html)
            if content_item:
                content_item.source_name = self.source_name
                self.logger.info(f"Successfully scraped: {content_item.title}")
                return content_item
            else:
                self.logger.warning(f"Failed to parse content from {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")
            return None
            
    async def scrape_all(self, max_items: int = 20) -> List[ContentItem]:
        """Scrape all available content up to max_items"""
        self.logger.info(f"Starting scrape for {self.source_name}")
        
        try:
            urls = await self.discover_urls()
            if not urls:
                self.logger.warning("No URLs discovered")
                return []
                
            # Limit URLs to max_items
            urls = urls[:max_items]
            self.logger.info(f"Discovered {len(urls)} URLs to scrape")
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await self.scrape_single_url(url)
                    
            # Execute scraping tasks
            tasks = [scrape_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            content_items = []
            for result in results:
                if isinstance(result, ContentItem):
                    content_items.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Task failed with exception: {result}")
                    
            self.logger.info(f"Successfully scraped {len(content_items)} items")
            return content_items
            
        except Exception as e:
            self.logger.error(f"Error in scrape_all: {e}")
            return []
            
    def validate_content_item(self, item: ContentItem) -> bool:
        """Validate that a content item meets minimum requirements"""
        if not item.title or len(item.title.strip()) < 10:
            return False
            
        if not item.content or len(item.content.strip()) < 100:
            return False
            
        if not item.url or not self.is_valid_url(item.url):
            return False
            
        return True
        
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
            
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except Exception:
            return ""