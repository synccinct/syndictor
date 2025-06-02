# RSS Feed Scraper Module
# src/scrapers/modules/rss_scraper.py

import feedparser
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dateutil.parser import parse as parse_date
from bs4 import BeautifulSoup
import re

from .base_scraper import BaseScraper, ContentItem

class RssScraper(BaseScraper):
    """Scraper for RSS feed sources"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.feed_urls = source_config.get("feed_urls", [])
        self.max_age_days = source_config.get("max_age_days", 7)
        self.min_content_length = source_config.get("min_content_length", 100)
        
    async def discover_urls(self) -> List[str]:
        """Discover article URLs from RSS feeds"""
        all_urls = []
        
        for feed_url in self.feed_urls:
            self.logger.info(f"Fetching RSS feed: {feed_url}")
            
            try:
                # Fetch RSS feed content
                feed_content = await self.fetch_url(feed_url)
                if not feed_content:
                    continue
                    
                # Parse feed with feedparser
                feed = feedparser.parse(feed_content)
                
                # Check if feed parsing was successful
                if not feed or not feed.entries:
                    self.logger.warning(f"No entries found in feed: {feed_url}")
                    continue
                    
                # Extract article URLs
                urls = []
                for entry in feed.entries:
                    if 'link' in entry:
                        urls.append(entry.link)
                        
                self.logger.info(f"Found {len(urls)} URLs in feed: {feed_url}")
                all_urls.extend(urls)
                
            except Exception as e:
                self.logger.error(f"Error processing feed {feed_url}: {e}")
                
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = [url for url in all_urls if not (url in seen or seen.add(url))]
        
        return unique_urls
        
    async def parse_content(self, url: str, html: str) -> Optional[ContentItem]:
        """Parse content from HTML and return ContentItem"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                self.logger.warning(f"No title found for {url}")
                return None
                
            # Extract content
            content = self._extract_content(soup)
            if not content or len(content) < self.min_content_length:
                self.logger.warning(f"Insufficient content for {url}")
                return None
                
            # Extract author
            author = self._extract_author(soup)
            
            # Extract publication date
            published_date = self._extract_date(soup)
            
            # Extract tags/categories
            tags = self._extract_tags(soup)
            
            # Extract summary
            summary = self._extract_summary(soup, content)
            
            # Create ContentItem
            content_item = ContentItem(
                title=title,
                content=content,
                url=url,
                author=author,
                published_date=published_date,
                tags=tags,
                summary=summary
            )
            
            if not self.validate_content_item(content_item):
                self.logger.warning(f"Content validation failed for {url}")
                return None
                
            return content_item
            
        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")
            return None
            
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from page"""
        # Try multiple approaches
        # 1. Check article header
        article_header = soup.find('h1', class_=re.compile('(title|header|heading)'))
        if article_header and article_header.text.strip():
            return article_header.text.strip()
            
        # 2. Check article tag
        article = soup.find('article')
        if article:
            header = article.find('h1')
            if header and header.text.strip():
                return header.text.strip()
                
        # 3. Check page title
        if soup.title and soup.title.text:
            title = soup.title.text.strip()
            # Remove site name from title
            if ' | ' in title:
                title = title.split(' | ')[0].strip()
            elif ' - ' in title:
                title = title.split(' - ')[0].strip()
                
            return title
            
        return ""
        
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Try multiple approaches
        # 1. Look for main article content
        main_content = None
        
        # Check for article tag
        article = soup.find('article')
        if article:
            main_content = article
            
        # Check for content with specific classes
        if not main_content:
            content_candidates = soup.find_all(['div', 'section'], class_=re.compile('(content|article|post)'))
            if content_candidates:
                # Choose the longest content
                main_content = max(content_candidates, key=lambda x: len(x.get_text()))
                
        # Extract text from main content
        if main_content:
            # Remove unwanted elements
            for unwanted in main_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                unwanted.decompose()
                
            # Extract text with paragraph structure
            content = ""
            for p in main_content.find_all('p'):
                p_text = p.get_text().strip()
                if p_text and len(p_text) > 20:  # Skip short paragraphs
                    content += p_text + "\n\n"
                    
            return content.strip()
            
        # Fallback: extract all paragraphs from body
        paragraphs = []
        for p in soup.find_all('p'):
            p_text = p.get_text().strip()
            if p_text and len(p_text) > 30:  # Only include substantial paragraphs
                paragraphs.append(p_text)
                
        return "\n\n".join(paragraphs)
        
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from page"""
        # Try multiple approaches
        # 1. Look for author metadata
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
            
        # 2. Look for author in schema.org markup
        author_elem = soup.find(['span', 'div', 'a'], {'itemprop': 'author'})
        if author_elem:
            author_name = author_elem.find({'itemprop': 'name'})
            if author_name:
                return author_name.text.strip()
            return author_elem.text.strip()
            
        # 3. Look for common author classes
        author_classes = ['author', 'byline', 'writer']
        for cls in author_classes:
            author_elem = soup.find(class_=re.compile(cls))
            if author_elem:
                return author_elem.text.strip()
                
        return None
        
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date from page"""
        # Try multiple approaches
        # 1. Look for time element
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            try:
                return parse_date(time_elem['datetime'])
            except ValueError:
                pass
                
        # 2. Look for metadata
        for meta in soup.find_all('meta'):
            if meta.get('property') in ['article:published_time', 'og:published_time']:
                try:
                    return parse_date(meta['content'])
                except ValueError:
                    pass
                    
        # 3. Look for dates in text
        date_classes = ['date', 'published', 'time', 'timestamp']
        for cls in date_classes:
            date_elem = soup.find(class_=re.compile(cls))
            if date_elem:
                try:
                    return parse_date(date_elem.text.strip())
                except ValueError:
                    pass
                    
        return None
        
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/categories from page"""
        tags = []
        
        # 1. Look for meta keywords
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].split(',')
            tags.extend([k.strip() for k in keywords if k.strip()])
            
        # 2. Look for tag elements
        tag_elements = soup.find_all(['a', 'span'], class_=re.compile('(tag|category)'))
        for tag in tag_elements:
            tag_text = tag.text.strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
                
        return tags
        
    def _extract_summary(self, soup: BeautifulSoup, content: str) -> Optional[str]:
        """Extract or generate summary"""
        # 1. Look for description meta tag
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
            
        # 2. Look for og:description
        og_desc = soup.find('meta', {'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
            
        # 3. Use first paragraph of content as summary
        if content:
            paragraphs = content.split('\n\n')
            if paragraphs:
                summary = paragraphs[0].strip()
                # Truncate if too long
                if len(summary) > 200:
                    return summary[:197] + '...'
                return summary
                
        return None