import requests
from bs4 import BeautifulSoup
from newspaper import Article
import re
from typing import Dict, Optional
import time
import random

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # Multiple User-Agents untuk rotasi random
        self.user_agents = [
            # Googlebot variants
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            
            # Bingbot variants  
            'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
            'Mozilla/5.0 (seoanalyzer; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
            
            # Other search engine bots
            'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
            'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
            'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            
            # Legitimate crawlers
            'Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)',
            'Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)',
            'Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)',
            
            # Chrome variants (legitimate browsers)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox variants
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0',
            
            # Safari variants
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            
            # Edge variants
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Mobile variants
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        
        # Set initial random user agent
        self._rotate_user_agent()
    
    def _rotate_user_agent(self):
        """Rotate user agent randomly"""
        selected_ua = random.choice(self.user_agents)
        
        self.session.headers.update({
            'User-Agent': selected_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',  # Prioritas Indonesia
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'  # Do Not Track
        })
        
        # Log user agent yang dipilih (untuk debugging)
        print(f"🔄 Using User-Agent: {selected_ua[:60]}...")
    
    def get_random_headers(self, url: str = None) -> Dict[str, str]:
        """Generate random headers with Indonesian language priority"""
        
        # Rotate user agent untuk setiap request
        user_agent = random.choice(self.user_agents)
        
        # Detect if it's a bot or browser for different header sets
        is_bot = any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'spider'])
        
        if is_bot:
            # Bot headers - simpler and more focused
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache'
            }
        else:
            # Browser headers - more comprehensive
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7,ms;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1'
            }
            
            # Add referer for some requests (make it look more natural)
            if random.random() < 0.3:  # 30% chance
                referers = [
                    'https://www.google.com/',
                    'https://www.google.co.id/',
                    'https://www.bing.com/',
                    'https://duckduckgo.com/'
                ]
                headers['Referer'] = random.choice(referers)
        
        return headers
    
    def get_title_newspaper3k(self, url: str) -> Optional[str]:
        """Get title using newspaper3k - primary method"""
        try:
            # Rotate user agent sebelum request
            self._rotate_user_agent()
            
            article = Article(url)
            article.download()
            article.parse()
            return article.title if article.title else None
        except Exception as e:
            print(f"Error getting title with newspaper3k for {url}: {str(e)}")
            # Fallback to manual extraction
            return self._get_title_manual(url)
    
    def _get_title_manual(self, url: str) -> Optional[str]:
        """Fallback title extraction"""
        try:
            headers = self.get_random_headers(url)
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple title selectors
            title_selectors = [
                'h1',
                'title',
                '.article-title',
                '.post-title',
                '.entry-title',
                '[property="og:title"]',
                '[name="twitter:title"]',
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                if selector.startswith('['):
                    element = soup.select_one(selector)
                    if element:
                        title = element.get('content') or element.get_text(strip=True)
                        if title and len(title) > 5:
                            return title
                else:
                    element = soup.select_one(selector)
                    if element and element.get_text(strip=True):
                        title = element.get_text(strip=True)
                        if len(title) > 5:
                            return title
            
            return "Gagal mengambil judul"
            
        except Exception as e:
            print(f"Error in manual title extraction: {str(e)}")
            return "Gagal mengambil judul"
    
    async def scrape_article(self, url: str, timeout: int = 30, basic_only: bool = False) -> Optional[Dict]:
        """Scrape article using requests + newspaper3k + BeautifulSoup"""
        return self.scrape_article_sync(url, timeout, basic_only)
    
    def scrape_article_sync(self, url: str, timeout: int = 30, basic_only: bool = False) -> Optional[Dict]:
        """Synchronous scraping method with random user agents"""
        try:
            # Add random delay to be respectful and avoid rate limiting
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)
            
            print(f"🌐 Scraping: {url[:60]}...")
            
            # Method 1: Try newspaper3k first (most reliable)
            article_data = self._scrape_with_newspaper3k(url)
            if article_data and len(article_data.get('content', '')) > 200:
                print(f"✅ Success with newspaper3k: {len(article_data.get('content', ''))} chars")
                return article_data
            
            # Method 2: Fallback to manual scraping
            print("🔄 Fallback to manual scraping...")
            return self._scrape_with_requests(url, timeout, basic_only)
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {str(e)}")
            return None
    
    def _scrape_with_newspaper3k(self, url: str) -> Optional[Dict]:
        """Primary method using newspaper3k with random UA"""
        try:
            # Rotate user agent
            self._rotate_user_agent()
            
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text.strip()) > 100:
                return {
                    'content': article.text.strip(),
                    'url': url,
                    'title': article.title or '',
                    'publish_date': str(article.publish_date) if article.publish_date else '',
                    'method': 'newspaper3k'
                }
            
            return None
            
        except Exception as e:
            print(f"📰 Newspaper3k failed for {url}: {str(e)}")
            return None
    
    def _scrape_with_requests(self, url: str, timeout: int = 30, basic_only: bool = False) -> Optional[Dict]:
        """Fallback method using requests + BeautifulSoup with random headers"""
        try:
            headers = self.get_random_headers(url)
            print(f"🔧 Using headers: {headers['User-Agent'][:50]}...")
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Check if we got meaningful content
            if len(response.content) < 1000:
                print(f"⚠️ Suspiciously small response: {len(response.content)} bytes")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data
            if basic_only:
                content = self._extract_content(soup)
                return {'content': content, 'url': url, 'method': 'requests_basic'}
            else:
                article_data = self._extract_article_data(soup, url)
                article_data['method'] = 'requests_full'
                return article_data
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error for {url}: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Error scraping with requests {url}: {str(e)}")
            return None
    
    def _extract_article_data(self, soup: BeautifulSoup, url: str) -> Dict:
        # Remove unwanted elements
        unwanted_elements = [
            'script', 'style', 'nav', 'header', 'footer', 
            'sidebar', 'advertisement', 'ads', 'menu',
            'noscript', 'iframe', 'form', 'button'
        ]
        
        for element_name in unwanted_elements:
            for element in soup.find_all(element_name):
                element.decompose()
        
        # Remove unwanted classes and IDs
        unwanted_selectors = [
            '.ad', '.ads', '.advertisement', '.social-share', 
            '.related-posts', '.comments', '.comment-section',
            '.sidebar', '.navigation', '.nav', '.menu',
            '#comments', '#sidebar', '#navigation'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract content
        content = self._extract_content(soup)
        
        return {
            'content': content,
            'url': url
        }
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try multiple selectors for article content (prioritized for Indonesian news sites)
        content_selectors = [
            # Generic article selectors
            'article',
            '[role="main"] article',
            
            # Common Indonesian news site patterns
            '.article-content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.post-body',
            '.content-body',
            '.detail-content',
            '.news-content',
            
            # Specific patterns with wildcards
            '[class*="article-content"]',
            '[class*="post-content"]',
            '[class*="entry-content"]',
            '[class*="detail-content"]',
            '[class*="news-content"]',
            
            # Broader selectors
            '.content',
            '[class*="content"]',
            'main article',
            'main .content',
            '.text',
            'main',
            
            # Fallback
            '.container article',
            '.wrapper article'
        ]
        
        best_content = ""
        
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Additional cleaning for Indonesian news sites
                    for unwanted in element.select('''
                        script, style, .ad, .ads, .advertisement, 
                        .social-share, .related-posts, .comments, 
                        .comment-section, nav, header, footer,
                        .breadcrumb, .tags, .category, .meta,
                        .share-buttons, .social-buttons
                    '''):
                        unwanted.decompose()
                    
                    text = element.get_text(separator=' ', strip=True)
                    
                    # Use the longest meaningful content
                    if len(text) > len(best_content) and len(text) > 200:
                        best_content = text
                        print(f"📄 Found content with selector '{selector}': {len(text)} chars")
            except Exception as e:
                print(f"⚠️ Error with selector '{selector}': {e}")
                continue
        
        # If no good content found, try paragraph extraction
        if len(best_content) < 200:
            print("🔍 Trying paragraph extraction...")
            paragraphs = soup.find_all('p')
            paragraph_texts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Skip very short paragraphs and common non-content patterns
                if (len(text) > 30 and 
                    not any(skip in text.lower() for skip in ['copyright', 'baca juga', 'lihat juga', 'follow', 'subscribe'])):
                    paragraph_texts.append(text)
            
            if paragraph_texts:
                best_content = ' '.join(paragraph_texts)
                print(f"📝 Paragraph extraction: {len(best_content)} chars")
        
        # Clean the content
        if best_content:
            # Remove multiple spaces and newlines
            best_content = re.sub(r'\s+', ' ', best_content)
            best_content = re.sub(r'\n+', '\n', best_content)
            
            # Remove common Indonesian news site artifacts
            artifacts = [
                r'Baca juga:.*?(?=\w)',
                r'Lihat juga:.*?(?=\w)', 
                r'ADVERTISEMENT',
                r'CONTINUE READING BELOW',
                r'Loading...',
                r'Tunggu sebentar...'
            ]
            
            for artifact in artifacts:
                best_content = re.sub(artifact, '', best_content, flags=re.IGNORECASE)
            
            best_content = best_content.strip()
        
        return best_content
    
    def get_user_agent_stats(self):
        """Get statistics about available user agents"""
        bot_count = sum(1 for ua in self.user_agents if any(bot in ua.lower() for bot in ['bot', 'crawler', 'spider']))
        browser_count = len(self.user_agents) - bot_count
        
        return {
            'total': len(self.user_agents),
            'bots': bot_count,
            'browsers': browser_count,
            'current': self.session.headers.get('User-Agent', 'Not set')[:60] + '...'
        }
