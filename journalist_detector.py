from newspaper import Article
from bs4 import BeautifulSoup
import re
from typing import Optional

class JournalistDetector:
    def __init__(self):
        pass

    def detect_journalist(self, url: str, content: str) -> Optional[str]:
        journalist = None
        
        # Method 1: Using newspaper3k
        journalist = self._detect_with_newspaper3k(url)
        
        if not journalist:
            # Method 2: Using BeautifulSoup patterns
            journalist = self._detect_with_patterns(content)
        
        return journalist if journalist else "Tidak ditemukan"

    def _detect_with_newspaper3k(self, url: str) -> Optional[str]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if hasattr(article, 'authors') and article.authors:
                return ', '.join(article.authors)
            
        except Exception as e:
            print(f"Error with newspaper3k: {str(e)}")
        
        return None

    def _detect_with_patterns(self, content: str) -> Optional[str]:
        # Common patterns for journalist names
        patterns = [
            r'(?:Oleh|By|Penulis|Reporter|Wartawan)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–—]\s*(?:Reporter|Wartawan|Jurnalis)',
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–—]\s*[A-Z][a-z]+',
            r'(?:Ditulis oleh|Written by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                # Return the first match that looks like a name
                for match in matches:
                    if len(match.split()) >= 2:  # At least first and last name
                        return match.strip()
        
        return None