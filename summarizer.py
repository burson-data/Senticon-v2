import google.generativeai as genai
from typing import Dict, Optional
import json
import re

class ArticleSummarizer:
    def __init__(self):
        self.api_key = None
        self.model = None

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def summarize_article(self, content: str, config: Dict) -> Optional[Dict]:
        if not self.model:
            return None
        
        try:
            prompt = self._create_summary_prompt(content, config)
            response = self.model.generate_content(prompt)
            
            # Parse response
            return self._parse_summary_response(response.text, config)
            
        except Exception as e:
            print(f"Error summarizing article: {str(e)}")
            return None

    def _create_summary_prompt(self, content: str, config: Dict) -> str:
        # Base prompt components
        summary_type = config.get('summary_type', 'Ringkas')
        max_length = config.get('max_length', 150)
        language = config.get('language', 'Bahasa Indonesia')
        focus_aspect = config.get('focus_aspect', '')
        
        # Limit content length to avoid token limits
        content = content[:4000] if len(content) > 4000 else content
        
        # Language instruction
        if language == "English":
            lang_instruction = "Respond in English."
        elif language == "Bahasa Indonesia":
            lang_instruction = "Respond in Bahasa Indonesia."
        else:  # "Sama dengan artikel"
            lang_instruction = "Use the same language as the original article."
        
        # Summary type instructions
        type_instructions = {
            'Ringkas': f"Create a concise summary in approximately {max_length} words that captures the main points.",
            'Detail': f"Create a detailed summary in approximately {max_length} words that includes important details and context.",
            'Poin-poin Utama': f"Create a bullet-point summary with the main points, keeping it under {max_length} words total.",
            'Custom': config.get('custom_instruction', f"Create a summary in approximately {max_length} words.")
        }
        
        type_instruction = type_instructions.get(summary_type, type_instructions['Ringkas'])
        
        # Focus aspect instruction
        focus_instruction = ""
        if focus_aspect:
            focus_instruction = f"\nFocus specifically on: {focus_aspect}"
        
        prompt = f"""
        Summarize the following article according to these requirements:
        
        REQUIREMENTS:
        - {type_instruction}
        - {lang_instruction}
        - Maximum {max_length} words
        {focus_instruction}
        
        ARTICLE:
        {content}
        
        Please provide only the summary text without any additional formatting or explanations.
        """
        
        return prompt

    def _parse_summary_response(self, response_text: str, config: Dict) -> Dict:
        try:
            summary = response_text.strip()
            word_count = self._count_words(summary)
            
            return {
                "summary": summary,
                "word_count": word_count
            }
        except Exception as e:
            print(f"Error parsing summary response: {str(e)}")
            return {
                "summary": "Gagal memparse ringkasan",
                "word_count": 0
            }

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())