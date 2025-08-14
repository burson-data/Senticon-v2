# app.py

import streamlit as st
import pandas as pd
from io import BytesIO
import asyncio
from datetime import datetime
import re
import os
from typing import List, Dict, Optional
import json

# Import modules (assuming these are correctly defined in their respective files)
from scraper import NewsScraper
from sentiment_analyzer import SentimentAnalyzer
from journalist_detector import JournalistDetector
from summarizer import ArticleSummarizer
from topic_modeller import TopicModeller # --- BARU ---
from config import GEMINI_API_KEY

class NewsAnalyzerApp:
def __init__(self):
    self.scraper = NewsScraper()
    self.sentiment_analyzer = SentimentAnalyzer()
    self.journalist_detector = JournalistDetector()
    self.summarizer = ArticleSummarizer()
    self.topic_modeller = TopicModeller() # --- BARU ---

    # Set API key from config
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        self.sentiment_analyzer.set_api_key(GEMINI_API_KEY)
        self.summarizer.set_api_key(GEMINI_API_KEY)
        self.topic_modeller.set_api_key(GEMINI_API_KEY) # --- BARU ---

def setup_page(self):
    st.set_page_config(
        page_title="News Analyzer",
        page_icon="📰",
        layout="wide"
    )

    st.title("📰 News Analyzer")
    st.markdown("Aplikasi untuk tarik full teks berita, analisis sentimen, deteksi jurnalis, summarize, dan penentuan topik artikel.") # --- MODIFIKASI ---

    # Show scraper info
    try:
        stats = self.scraper.get_user_agent_stats()
        st.info(f"🔄 Scraper ready: {stats['total']} User-Agents (Bots: {stats['bots']}, Browsers: {stats['browsers']}) | Bahasa: Indonesia Priority")
    except:
        st.info("🔄 Menggunakan Newspaper3k + BeautifulSoup dengan multiple User-Agents dan prioritas Bahasa Indonesia")

def setup_sidebar(self):
    st.sidebar.header("⚙️ Konfigurasi")

    # Feature Selection
    st.sidebar.subheader("🎯 Pilih Fungsi yang Digunakan")

    enable_scraping = st.sidebar.checkbox(
        "📄 Tarik Full Teks Berita",
        value=True,
        help="Mengambil konten lengkap berita dari URL"
    )

    enable_sentiment = st.sidebar.checkbox(
        "😊 Analisis Sentimen",
        value=False,
        help="Menganalisis sentimen berdasarkan konteks"
    )

    enable_journalist = st.sidebar.checkbox(
        "👤 Deteksi Jurnalis",
        value=False,
        help="Mendeteksi nama penulis/jurnalis"
    )

    enable_summarize = st.sidebar.checkbox(
        "📝 Summarize Artikel",
        value=False,
        help="Membuat ringkasan artikel menggunakan AI"
    )

    # --- FITUR BARU: PENENTUAN TOPIK ---
    enable_topic = st.sidebar.checkbox(
        "📊 Penentuan Topik",
        value=False,
        help="Menentukan topik artikel menggunakan AI"
    )

    st.sidebar.markdown("---")

    # Conditional configurations
    sentiment_context = None
    summarize_config = {}
    topic_config = {} # --- BARU ---

    # Topic Configuration (only show if enabled)
    if enable_topic: # --- BARU ---
        st.sidebar.subheader("📊 Konfigurasi Topik")
        topic_config['mode'] = st.sidebar.radio(
            "Mode Penentuan Topik",
            options=["Ditentukan AI", "Ditentukan User", "Hybrid"],
            index=0,
            help=(
                "- **Ditentukan AI**: AI akan menentukan topik secara otomatis.\n"
                "- **Ditentukan User**: AI akan memilih dari daftar topik yang Anda berikan.\n"
                "- **Hybrid**: AI akan mencoba mencocokkan dari daftar Anda, jika tidak ada yang cocok, AI akan menentukan sendiri."
            )
        )

        if topic_config['mode'] in ["Ditentukan User", "Hybrid"]:
            user_topics_input = st.sidebar.text_area(
                "Daftar Topik (pisahkan dengan koma)",
                placeholder="Contoh: Politik, Ekonomi, Olahraga, Teknologi, Kesehatan",
                help="Masukkan daftar topik yang bisa dipilih."
            )
            topic_config['user_topics'] = [topic.strip() for topic in user_topics_input.split(',') if topic.strip()]
        else:
            topic_config['user_topics'] = []

    # Sentiment Configuration (only show if enabled)
    if enable_sentiment:
        st.sidebar.subheader("😊 Konfigurasi Sentimen")
        sentiment_context = st.sidebar.text_area(
            "Konteks Sentimen",
            placeholder="Contoh: Toyota Avanza, harga mobil, kualitas produk",
            help="Masukkan objek/aspek untuk analisis sentimen"
        )

    # Summarize Configuration (only show if enabled)
    if enable_summarize:
        st.sidebar.subheader("📝 Konfigurasi Summarize")
        summarize_config = {
            'summary_type': st.sidebar.selectbox(
                "Tipe Ringkasan",
                ["Ringkas", "Detail", "Poin-poin Utama", "Custom"],
                help="Pilih jenis ringkasan yang diinginkan"
            ),
            'max_length': st.sidebar.slider(
                "Panjang Maksimal (kata)",
                min_value=50, max_value=500, value=150, step=25,
                help="Jumlah kata maksimal dalam ringkasan"
            ),
            'language': st.sidebar.selectbox(
                "Bahasa Ringkasan",
                ["Bahasa Indonesia", "English", "Sama dengan artikel"],
                help="Bahasa yang digunakan untuk ringkasan"
            ),
            'focus_aspect': st.sidebar.text_input(
                "Aspek yang Difokuskan (Opsional)",
                placeholder="Contoh: aspek ekonomi, dampak sosial",
                help="Aspek tertentu yang ingin difokuskan dalam ringkasan"
            )
        }

        if summarize_config['summary_type'] == 'Custom':
            summarize_config['custom_instruction'] = st.sidebar.text_area(
                "Instruksi Custom",
                placeholder="Contoh: Buat ringkasan dalam format bullet points...",
                help="Instruksi khusus untuk pembuatan ringkasan"
            )

    # Scraping options
    if enable_scraping:
        st.sidebar.subheader("🔧 Opsi Scraping")
        scraping_timeout = st.sidebar.slider(
            "Timeout (detik)", min_value=10, max_value=60, value=30,
            help="Waktu tunggu maksimal untuk setiap URL"
        )
    else:
        scraping_timeout = 30

    return {
        'enable_scraping': enable_scraping,
        'enable_sentiment': enable_sentiment,
        'enable_journalist': enable_journalist,
        'enable_summarize': enable_summarize,
        'enable_topic': enable_topic, # --- BARU ---
        'sentiment_context': sentiment_context,
        'summarize_config': summarize_config,
        'topic_config': topic_config, # --- BARU ---
        'scraping_timeout': scraping_timeout
    }

def get_column_mapping(self, df: pd.DataFrame, input_method: str):
    st.subheader("📋 Mapping Kolom")
    st.info("Pilih kolom yang sesuai dari file Excel Anda")

    col1, col2 = st.columns(2)

    with col1:
        url_column = st.selectbox(
            "Kolom URL",
            options=df.columns.tolist(),
            index=0 if 'URL' in df.columns else (df.columns.tolist().index('Link') if 'Link' in df.columns else 0), # Added 'Link' check
            help="Pilih kolom yang berisi URL artikel"
        )

    with col2:
        snippet_column = st.selectbox(
            "Kolom Snippet (Opsional)",
            options=["Tidak Ada"] + df.columns.tolist(),
            index=df.columns.tolist().index('Snippet') + 1 if 'Snippet' in df.columns else 0,
            help="Pilih kolom yang berisi snippet/ringkasan artikel"
        )

    return {
        'url_column': url_column,
        'snippet_column': snippet_column if snippet_column != "Tidak Ada" else None
    }

def process_urls_manual(self, urls: List[str], config: Dict) -> List[Dict]:
    """Process manual URL input"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, url in enumerate(urls):
        status_text.text(f"Memproses URL {i+1}/{len(urls)}: {url[:50]}...")

        try:
            result = {'URL': url}
            content = ""

            title = self.scraper.get_title_newspaper3k(url)
            result['Title'] = title if title else 'Gagal mengambil judul'
            if config['enable_scraping']:
                article_data = self.scraper.scrape_article_sync(
                    url, timeout=config['scraping_timeout']
                )
                if article_data:
                    result['Content'] = article_data.get('content', '')
                    result['Scraping_Method'] = article_data.get('method', 'unknown')
                    content = article_data.get('content', '')
                else:
                    result['Content'] = 'Gagal scraping'
                    result['Scraping_Method'] = 'failed'
                    content = ''
            else:
                try:
                    article_data = self.scraper.scrape_article_sync(url, basic_only=True)
                    content = article_data.get('content', '') if article_data else ''
                except:
                    content = ''

            analysis_text = content

            # 2. Journalist Detection
            if config['enable_journalist']:
                if analysis_text:
                    result['Journalist'] = self.journalist_detector.detect_journalist(url, analysis_text)
                else:
                    result['Journalist'] = 'Tidak ada konten'

            # 3. Sentiment Analysis
            if config['enable_sentiment'] and config['sentiment_context']:
                if analysis_text and len(analysis_text.strip()) > 5:
                    sentiment = self.sentiment_analyzer.analyze_sentiment(
                        analysis_text, config['sentiment_context']
                    )
                    if sentiment:
                        result.update({
                            'Sentiment': sentiment.get('sentiment', 'Gagal'),
                            'Confidence': sentiment.get('confidence', ''),
                            'Reasoning': sentiment.get('reasoning', '')
                        })
                    else:
                         result.update({'Sentiment': 'Gagal Analisis AI'})
                else:
                    result.update({'Sentiment': 'Konten tidak cukup'})

            # 4. Summarize
            if config['enable_summarize']:
                if analysis_text and len(analysis_text.strip()) > 50:
                    summary = self.summarizer.summarize_article(
                        analysis_text, config['summarize_config']
                    )
                    result['Summary'] = summary.get('summary', 'Gagal summarize') if summary else 'Gagal summarize'
                else:
                    result['Summary'] = 'Konten terlalu pendek'

            # 5. Topic Modelling --- BARU ---
            if config['enable_topic']:
                if analysis_text and len(analysis_text.strip()) > 50:
                    topic = self.topic_modeller.determine_topic(
                        analysis_text, config['topic_config']
                    )
                    result['Topic'] = topic
                else:
                    result['Topic'] = 'Konten terlalu pendek'

        except Exception as e:
            result = {'URL': url, 'Title': f'Error: {str(e)}'}
            status_text.text(f"❌ Error: {url[:30]}... - {str(e)[:50]}...")

        results.append(result)
        progress_bar.progress((i + 1) / len(urls))

    status_text.text("Selesai!")
    return results

def process_excel_data(self, df: pd.DataFrame, column_mapping: Dict, config: Dict) -> pd.DataFrame:
    """Process Excel file data"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_rows = len(df)

    for i, row in df.iterrows():
        status_text.text(f"Menganalisis baris {i+1}/{total_rows}...")

        result = row.to_dict()

        url = row.get(column_mapping['url_column'], '')
        snippet = ""
        content = ""
        if column_mapping['snippet_column']:
            snippet = str(row.get(column_mapping['snippet_column'], ''))
            if snippet == 'nan': snippet = ""
        if url:
            title = self.scraper.get_title_newspaper3k(url)
            if title: result['Title_New'] = title
        if config['enable_scraping'] and url:
            try:
                article_data = self.scraper.scrape_article_sync(
                    url, timeout=config['scraping_timeout']
                )
                if article_data:
                    result['Content_New'] = article_data.get('content', '')
                    result['Scraping_Method_New'] = article_data.get('method', 'unknown')
                    content = article_data.get('content', '')
                else:
                    result['Content_New'] = 'Gagal scraping'
                    result['Scraping_Method_New'] = 'failed'
            except Exception as e:
                result['Content_New'] = f'Error scraping: {str(e)}'
                result['Scraping_Method_New'] = 'error'

        analysis_text = content if content and len(content.strip()) > 10 else snippet

        # 2. Journalist Detection
        if config['enable_journalist']:
            if analysis_text:
                result['Journalist_New'] = self.journalist_detector.detect_journalist(url, analysis_text)
            else:
                result['Journalist_New'] = 'Tidak ada konten'

        # 3. Sentiment Analysis
        if config['enable_sentiment'] and config['sentiment_context']:
            if analysis_text and len(analysis_text.strip()) > 5:
                sentiment = self.sentiment_analyzer.analyze_sentiment(
                    analysis_text, config['sentiment_context']
                )
                if sentiment:
                    result.update({
                        'Sentiment_New': sentiment.get('sentiment', 'Gagal'),
                        'Confidence_New': sentiment.get('confidence', ''),
                        'Reasoning_New': sentiment.get('reasoning', '')
                    })
                else:
                    result.update({'Sentiment_New': 'Gagal Analisis AI'})
            else:
                result.update({'Sentiment_New': 'Konten tidak cukup'})

        # 4. Summarize
        if config['enable_summarize']:
            if analysis_text and len(analysis_text.strip()) > 50:
                summary = self.summarizer.summarize_article(
                    analysis_text, config['summarize_config']
                )
                result['Summary_New'] = summary.get('summary', 'Gagal summarize') if summary else 'Gagal summarize'
            else:
                result['Summary_New'] = 'Konten terlalu pendek'

        # 5. Topic Modelling --- BARU ---
        if config['enable_topic']:
            if analysis_text and len(analysis_text.strip()) > 50:
                topic = self.topic_modeller.determine_topic(
                    analysis_text, config['topic_config']
                )
                result['Topic_New'] = topic
            else:
                result['Topic_New'] = 'Konten terlalu pendek'

        results.append(result)
        progress_bar.progress((i + 1) / total_rows)

    status_text.text("Analisis selesai!")
    return pd.DataFrame(results)

def display_results(self, results, config: Dict, is_excel_data: bool = False):
    if isinstance(results, pd.DataFrame):
        df = results
        success_count = len(df)
    else:
        if not results:
            st.warning("Tidak ada hasil untuk ditampilkan.")
            return
        df = pd.DataFrame(results)
        # Assuming 'Content' column exists for manual URL processing
        success_count = len([r for r in results if r.get('Content', '') != '' or r.get('Content_New', '') != ''])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Data", len(df))
    with col2:
        st.metric("Berhasil", success_count)
    with col3:
        st.metric("Gagal", len(df) - success_count)
    with col4:
        st.metric("Waktu Proses", f"{datetime.now().strftime('%H:%M:%S')}") # Placeholder, actual time tracking needed

    st.info(f"📊 **Metode Scraping:** {'Diaktifkan' if config.get('enable_scraping') else 'Dinonaktifkan'}")

    enabled_features = []
    if config.get('enable_scraping'): enabled_features.append("📄 Full Teks")
    if config.get('enable_topic'): enabled_features.append("📊 Topik") # --- BARU ---
    if config.get('enable_sentiment'): enabled_features.append("😊 Sentimen")
    if config.get('enable_journalist'): enabled_features.append("👤 Jurnalis")
    if config.get('enable_summarize'): enabled_features.append("📝 Summarize")

    st.info(f"**Fungsi yang digunakan:** {' | '.join(enabled_features)}")

    if success_count > 0:
        st.subheader("📤 Export Data")
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"news_analysis_results_{timestamp}.xlsx"

        # Convert DataFrame to Excel in memory
        output = BytesIO()
        df.to_excel(output, index=False)
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Hasil Analisis (Excel)",
            data=processed_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_results"
        )

    st.subheader("📋 Preview Hasil")
    # THIS IS THE MISSING PART: Display the DataFrame
    st.dataframe(df)

def validate_configuration(self, config: Dict, urls: List[str], uploaded_file=None) -> List[str]:
    warnings = []

    if not any([
        config['enable_scraping'], config['enable_sentiment'],
        config['enable_journalist'], config['enable_summarize'],
        config['enable_topic']
    ]):
        warnings.append("⚠️ Pilih minimal satu fungsi untuk digunakan")

    if not GEMINI_API_KEY and any([
        config['enable_sentiment'], config['enable_summarize'], config['enable_topic']
    ]):
        features = []
        if config['enable_sentiment']: features.append("analisis sentimen")
        if config['enable_summarize']: features.append("summarize")
        if config['enable_topic']: features.append("penentuan topik") # --- BARU ---
        warnings.append(f"⚠️ API Key Gemini belum dikonfigurasi untuk {', '.join(features)}")

    if config['enable_sentiment']:
        if not config['sentiment_context']:
            warnings.append("⚠️ Konteks sentimen diperlukan untuk analisis sentimen")

    if config['enable_topic']:
        topic_cfg = config.get('topic_config', {})
        if topic_cfg.get('mode') in ["Ditentukan User", "Hybrid"]:
            if not topic_cfg.get('user_topics'):
                warnings.append("⚠️ Daftar topik diperlukan untuk mode 'Ditentukan User' atau 'Hybrid'")

    if not uploaded_file and not urls:
        warnings.append("⚠️ Masukkan minimal satu URL atau upload file Excel")

    return warnings

def run(self):
  self.setup_page()
  config = self.setup_sidebar()

  # Main content area
  st.header("📝 Input Data")

  # Input methods
  input_method = st.radio(
      "Pilih metode input:",
      ["URL Manual", "Upload File Excel"],
      horizontal=True
  )

  urls = []
  uploaded_file = None
  df = None
  column_mapping = {}

  if input_method == "URL Manual":
      url_input = st.text_area(
          "Masukkan URL (satu URL per baris):",
          height=200,
          placeholder="https://example.com/news1\nhttps://example.com/news2\nhttps://example.com/news3"
      )

      if url_input:
          urls = [url.strip() for url in url_input.split('\n') if url.strip()]
          st.info(f"Ditemukan {len(urls)} URL")

  else:  # Upload File Excel
      uploaded_file = st.file_uploader(
          "Upload file Excel",
          type=['xlsx', 'xls'],
          help="File Excel harus memiliki kolom URL"
      )

      if uploaded_file:
          try:
              df = pd.read_excel(uploaded_file)
              st.success(f"✅ Berhasil membaca {len(df)} baris data dari file")

              # Get column mapping
              column_mapping = self.get_column_mapping(df, input_method)

              # Show preview
              with st.expander("👀 Preview Data Input"): # Changed title to avoid confusion with results preview
                  st.dataframe(df.head(10))
                  if len(df) > 10:
                      st.info(f"... dan {len(df)-10} baris lainnya")

          except Exception as e:
              st.error(f"❌ Error membaca file: {str(e)}")

  # Validation
  warnings = self.validate_configuration(config, urls, uploaded_file)

  if warnings:
      for warning in warnings:
          st.warning(warning)

  # Process button
  can_process = not warnings

  if st.button(
      "🚀 Mulai Analisis",
      disabled=not can_process,
      use_container_width=True,
      type="primary"
  ):
      st.header("📊 Hasil Analisis")

      with st.spinner("Memproses data... Mohon tunggu"):
          if input_method == "URL Manual":
              results = self.process_urls_manual(urls, config)
              self.display_results(results, config, is_excel_data=False)
          else:
              results = self.process_excel_data(df, column_mapping, config)
              self.display_results(results, config, is_excel_data=True)
if __name__ == "__main__":
app = NewsAnalyzerApp()
app.run()
