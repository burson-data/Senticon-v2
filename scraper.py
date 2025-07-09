from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup
from newspaper import Article
import re
from typing import Dict, Optional
import asyncio

class NewsScraper:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

    def get_title_newspaper3k(self, url: str) -> Optional[str]:
        """Get title using newspaper3k"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.title if article.title else None
        except Exception as e:
            print(f"Error getting title with newspaper3k for {url}: {str(e)}")
            return None

    async def scrape_article(self, url: str, timeout: int = 30, basic_only: bool = False) -> Optional[Dict]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    java_script_enabled=False
                )
                
                page = await context.new_page()
                await stealth_async(page)
                
                # Navigate to URL
                await page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
                
                # Get HTML content
                html_content = await page.content()
                await browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract data
                if basic_only:
                    content = self._extract_content(soup)
                    return {'content': content, 'url': url}
                else:
                    article_data = self._extract_article_data(soup, url)
                    return article_data
                
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def _extract_article_data(self, soup: BeautifulSoup, url: str) -> Dict:
        # Remove unwanted elements
        unwanted_elements = ['script', 'style', 'nav', 'header', 'footer', 'sidebar', 'advertisement', 'ads', 'menu']
        
        for element_selector in unwanted_elements:
            elements = soup.find_all(element_selector)
            for element in elements:
                element.decompose()
        
        # Extract content
        content = self._extract_content(soup)
        
        return {
            'content': content,
            'url': url
        }

    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try multiple selectors for article content
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.content',
            '.article-body',
            '.entry-content',
            '[class*="content"]',
            '.text',
            'main'
        ]
        
        content_text = ""
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Remove unwanted nested elements
                for unwanted in element.select('script, style, .ad, .advertisement, .social-share, .related-posts'):
                    unwanted.decompose()
                
                text = element.get_text(separator=' ', strip=True)
                if len(text) > len(content_text):
                    content_text = text
        
        # If no content found, try paragraph extraction
        if not content_text:
            paragraphs = soup.find_all('p')
            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Clean the content
        content_text = re.sub(r'\s+', ' ', content_text)
        content_text = re.sub(r'\n+', '\n', content_text)
        
        return content_text.strip()
