# topic_modeller.py

import google.generativeai as genai
from typing import Dict, Optional, List
import json
import re

class TopicModeller:
    def __init__(self):
        """Initializes the TopicModeller."""
        self.api_key = None
        self.model = None

    def set_api_key(self, api_key: str):
        """Sets the API key and configures the Generative AI model."""
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def determine_topic(self, content: str, config: Dict) -> Optional[str]:
        """
        Determines the topic of the article based on the provided configuration.

        Args:
            content: The text content of the article.
            config: A dictionary containing topic modelling configuration,
                    including 'mode', and 'user_topics'.

        Returns:
            The determined topic as a string, or an error message.
        """
        if not self.model:
            return "Model AI tidak dikonfigurasi"

        try:
            prompt = self._create_prompt(content, config)
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error determining topic: {str(e)}")
            return "Gagal menentukan topik"

    def _create_prompt(self, content: str, config: Dict) -> str:
        """Creates a prompt for the AI based on the selected mode."""
        mode = config.get('mode', 'Ditentukan AI')
        user_topics = config.get('user_topics', [])
        
        # Limit content to avoid token limits
        truncated_content = content[:3500]

        if mode == 'Ditentukan User':
            return self._create_user_defined_prompt(truncated_content, user_topics)
        elif mode == 'Hybrid':
            return self._create_hybrid_prompt(truncated_content, user_topics)
        else: # 'Ditentukan AI'
            return self._create_ai_defined_prompt(truncated_content)

    def _create_user_defined_prompt(self, content: str, topics: List[str]) -> str:
        """Prompt to force a choice from a user-defined list."""
        return f"""
        Analisis artikel berikut dan tentukan topiknya HANYA dari daftar yang diberikan.
        Pilih salah satu topik yang paling relevan.

        DAFTAR TOPIK: {', '.join(topics)}

        ARTIKEL:
        {content}

        Jawaban Anda HARUS salah satu dari daftar topik di atas. Jangan berikan penjelasan, hanya nama topiknya.
        """

    def _create_ai_defined_prompt(self, content: str) -> str:
        """Prompt for the AI to define the topic freely."""
        return f"""
        Analisis artikel berikut dan tentukan topik utamanya dalam 1-3 kata.
        Contoh: "Politik Nasional", "Teknologi Smartphone", "Kesehatan Mental", "Sepak Bola Liga Inggris".

        ARTIKEL:
        {content}

        Berikan hanya nama topiknya saja.
        """

    def _create_hybrid_prompt(self, content: str, topics: List[str]) -> str:
        """
        Prompt for hybrid mode: try user list first, then define a new one 
        if no match is found.
        """
        return f"""
        Analisis artikel berikut. Pertama, coba cocokkan topiknya dengan salah satu dari DAFTAR TOPIK di bawah ini.
        Jika ada yang cocok, gunakan topik dari daftar tersebut.
        Jika tidak ada yang cocok sama sekali, tentukan sendiri topik yang paling sesuai dalam 1-3 kata.

        DAFTAR TOPIK: {', '.join(topics)}

        ARTIKEL:
        {content}
        
        Berikan jawaban akhir hanya berupa nama topiknya saja, tanpa penjelasan tambahan.
        """

    def _parse_response(self, response_text: str) -> str:
        """Parses the plain text response from the AI to get the topic."""
        # Simple cleaning: remove potential markdown and extra whitespace
        topic = response_text.replace('*', '').strip()
        return topic if topic else "Tidak dapat di-parse"
