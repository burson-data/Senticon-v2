import google.generativeai as genai
from typing import Dict, Optional
import json
import re

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = None
        self.model = None
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_sentiment(self, content: str, context: str) -> Optional[Dict]:
        if not self.model:
            return None
        
        try:
            prompt = self._create_sentiment_prompt(content, context)
            response = self.model.generate_content(prompt)
            
            # Parse response
            return self._parse_sentiment_response(response.text)
            
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return None
    
    def _create_sentiment_prompt(self, content: str, context: str) -> str:
        prompt = f"""
        Analisis sentimen dari artikel berita berikut berdasarkan konteks yang diberikan.
        
        KONTEKS: {context}
        
        ARTIKEL:
        {content[:3000]}  # Limit content to avoid token limits
        
        Berikan analisis sentimen dalam format JSON dengan struktur berikut:
        {{
            "sentiment": "positif/negatif/netral",
            "confidence": "tinggi/sedang/rendah",
            "reasoning": "penjelasan singkat mengapa sentimen tersebut dipilih berdasarkan konteks"
        }}
        
        Fokus analisis hanya pada konteks yang diberikan. Jika konteks tidak ditemukan dalam artikel, berikan sentimen "tidak terkait".
        """
        
        return prompt
    
    def _parse_sentiment_response(self, response_text: str) -> Dict:
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing
                sentiment = "netral"
                confidence = "rendah"
                reasoning = response_text
                
                if "positif" in response_text.lower():
                    sentiment = "positif"
                elif "negatif" in response_text.lower():
                    sentiment = "negatif"
                
                return {
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
        except:
            return {
                "sentiment": "netral",
                "confidence": "rendah",
                "reasoning": "Gagal menganalisis sentimen"
            }