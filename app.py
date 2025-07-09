import streamlit as st
import pandas as pd
from io import BytesIO
import asyncio
from datetime import datetime
import re
import os
from typing import List, Dict, Optional
import json

# Import modules
from scraper import NewsScraper
from sentiment_analyzer import SentimentAnalyzer
from journalist_detector import JournalistDetector
from summarizer import ArticleSummarizer
from config import GEMINI_API_KEY

class NewsAnalyzerApp:
 def __init__(self):
     self.scraper = NewsScraper()
     self.sentiment_analyzer = SentimentAnalyzer()
     self.journalist_detector = JournalistDetector()
     self.summarizer = ArticleSummarizer()
     
     # Set API key from config
     if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
         self.sentiment_analyzer.set_api_key(GEMINI_API_KEY)
         self.summarizer.set_api_key(GEMINI_API_KEY)
 
 def setup_page(self):
     st.set_page_config(
         page_title="News Analyzer",
         page_icon="📰",
         layout="wide"
     )
     
     st.title("📰 News Analyzer")
     st.markdown("Aplikasi untuk tarik full teks berita, analisis sentimen, deteksi jurnalis, dan summarize artikel")
     
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
     
     st.sidebar.markdown("---")
     
     # Conditional configurations
     sentiment_context = None
     summarize_config = {}
     
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
                 min_value=50,
                 max_value=500,
                 value=150,
                 step=25,
                 help="Jumlah kata maksimal dalam ringkasan"
             ),
             'language': st.sidebar.selectbox(
                 "Bahasa Ringkasan",
                 ["Bahasa Indonesia", "English", "Sama dengan artikel"],
                 help="Bahasa yang digunakan untuk ringkasan"
             ),
             'focus_aspect': st.sidebar.text_input(
                 "Aspek yang Difokuskan (Opsional)",
                 placeholder="Contoh: aspek ekonomi, dampak sosial, analisis teknis",
                 help="Aspek tertentu yang ingin difokuskan dalam ringkasan"
             )
         }
         
         if summarize_config['summary_type'] == 'Custom':
             summarize_config['custom_instruction'] = st.sidebar.text_area(
                 "Instruksi Custom",
                 placeholder="Contoh: Buat ringkasan dalam format bullet points dengan fokus pada angka dan statistik",
                 help="Instruksi khusus untuk pembuatan ringkasan"
             )
     
     # Scraping options
     if enable_scraping:
         st.sidebar.subheader("🔧 Opsi Scraping")
         scraping_timeout = st.sidebar.slider(
             "Timeout (detik)",
             min_value=10,
             max_value=60,
             value=30,
             help="Waktu tunggu maksimal untuk setiap URL"
         )
     else:
         scraping_timeout = 30
     
     return {
         'enable_scraping': enable_scraping,
         'enable_sentiment': enable_sentiment,
         'enable_journalist': enable_journalist,
         'enable_summarize': enable_summarize,
         'sentiment_context': sentiment_context,
         'summarize_config': summarize_config,
         'scraping_timeout': scraping_timeout
     }
 
 def get_column_mapping(self, df: pd.DataFrame, input_method: str):
     """Get column mapping for Excel files"""
     if input_method != "Upload File Excel":
         return {}
     
     st.subheader("📋 Mapping Kolom")
     st.info("Pilih kolom yang sesuai dari file Excel Anda")
     
     col1, col2 = st.columns(2)
     
     with col1:
         url_column = st.selectbox(
             "Kolom URL",
             options=df.columns.tolist(),
             index=0 if 'URL' in df.columns else 0,
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
             
             # Get title using newspaper3k first
             title = self.scraper.get_title_newspaper3k(url)
             result['Title'] = title if title else 'Gagal mengambil judul'
             
             # 1. Scraping (if enabled)
             if config['enable_scraping']:
                 # Use sync method instead of async
                 article_data = self.scraper.scrape_article_sync(
                     url, 
                     timeout=config['scraping_timeout']
                 )
                 
                 if article_data:
                     result['Content'] = article_data.get('content', '')
                     result['Scraping_Method'] = article_data.get('method', 'unknown')  # Track method
                     content = article_data.get('content', '')
                     
                     # Show success info
                     if len(content) > 500:
                         status_text.text(f"✅ Berhasil: {len(content)} karakter dari {url[:30]}...")
                     else:
                         status_text.text(f"⚠️ Konten pendek: {len(content)} karakter dari {url[:30]}...")
                 else:
                     result['Content'] = 'Gagal scraping'
                     result['Scraping_Method'] = 'failed'
                     content = ''
                     status_text.text(f"❌ Gagal scraping: {url[:30]}...")
             else:
                 # If scraping disabled, try to get basic content for other functions
                 try:
                     article_data = self.scraper.scrape_article_sync(url, basic_only=True)
                     content = article_data.get('content', '') if article_data else ''
                 except:
                     content = ''
             
             # 2. Journalist Detection (if enabled)
             if config['enable_journalist']:
                 if content:
                     journalist = self.journalist_detector.detect_journalist(url, content)
                     result['Journalist'] = journalist
                 else:
                     result['Journalist'] = 'Tidak dapat dideteksi (tidak ada konten)'
             
             # 3. Sentiment Analysis (if enabled)
             if config['enable_sentiment'] and config['sentiment_context']:
                 if content and len(content.strip()) > 5:
                     sentiment = self.sentiment_analyzer.analyze_sentiment(
                         content, config['sentiment_context']
                     )
                     
                     if sentiment:
                         result.update({
                             'Sentiment': sentiment.get('sentiment', ''),
                             'Confidence': sentiment.get('confidence', ''),
                             'Reasoning': sentiment.get('reasoning', '')
                         })
                     else:
                         result.update({
                             'Sentiment': 'Gagal analisis',
                             'Confidence': '',
                             'Reasoning': 'Error dalam analisis AI'
                         })
                 else:
                     result.update({
                         'Sentiment': 'Artikel tidak dapat dibuka',
                         'Confidence': '',
                         'Reasoning': 'Tidak ada konten yang cukup untuk analisis'
                     })
             
             # 4. Summarize (if enabled)
             if config['enable_summarize']:
                 if content and len(content.strip()) > 50:
                     summary = self.summarizer.summarize_article(
                         content, config['summarize_config']
                     )
                     
                     if summary:
                         result['Summary'] = summary.get('summary', '')
                     else:
                         result['Summary'] = 'Gagal membuat ringkasan'
                 else:
                     result['Summary'] = 'Konten terlalu pendek untuk diringkas'
             
         except Exception as e:
             result = {
                 'URL': url,
                 'Title': f'Error: {str(e)}',
                 'Content': '',
                 'Scraping_Method': 'error',
                 'Journalist': '',
                 'Sentiment': '',
                 'Confidence': '',
                 'Reasoning': '',
                 'Summary': ''
             }
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
         
         result = row.to_dict()  # Start with existing data
         
         url = row.get(column_mapping['url_column'], '')
         snippet = ""
         content = ""
         
         # Get snippet if column is specified
         if column_mapping['snippet_column']:
             snippet = str(row.get(column_mapping['snippet_column'], ''))
             if snippet == 'nan':
                 snippet = ""
         
         # Get title using newspaper3k for Excel data too
         if url:
             title = self.scraper.get_title_newspaper3k(url)
             if title:
                 result['Title_New'] = title
         
         # 1. Scraping (if enabled)
         if config['enable_scraping'] and url:
             try:
                 # Use sync method
                 article_data = self.scraper.scrape_article_sync(
                     url, 
                     timeout=config['scraping_timeout']
                 )
                 
                 if article_data:
                     result['Content_New'] = article_data.get('content', '')
                     result['Scraping_Method_New'] = article_data.get('method', 'unknown')  # Track method
                     content = article_data.get('content', '')
                     
                     # Show progress with method info
                     method = article_data.get('method', 'unknown')
                     status_text.text(f"✅ Baris {i+1}/{total_rows} - Method: {method} - {len(content)} chars")
                 else:
                     result['Content_New'] = 'Gagal scraping'
                     result['Scraping_Method_New'] = 'failed'
                     content = ''
                     status_text.text(f"❌ Baris {i+1}/{total_rows} - Scraping gagal")
             except Exception as e:
                 result['Content_New'] = f'Error scraping: {str(e)}'
                 result['Scraping_Method_New'] = 'error'
                 content = ''
                 status_text.text(f"❌ Baris {i+1}/{total_rows} - Error: {str(e)[:30]}...")
         
         # Determine text for analysis (prioritize content, then snippet)
         analysis_text = content if content and len(content.strip()) > 10 else snippet
         
         # 2. Journalist Detection (if enabled)
         if config['enable_journalist']:
             if analysis_text:
                 journalist = self.journalist_detector.detect_journalist(url, analysis_text)
                 result['Journalist_New'] = journalist
             else:
                 result['Journalist_New'] = 'Tidak ada konten untuk analisis'
         
         # 3. Sentiment Analysis (if enabled)
         if config['enable_sentiment'] and config['sentiment_context']:
             if analysis_text and len(analysis_text.strip()) > 5:
                 sentiment = self.sentiment_analyzer.analyze_sentiment(
                     analysis_text, config['sentiment_context']
                 )
                 
                 if sentiment:
                     result.update({
                         'Sentiment_New': sentiment.get('sentiment', ''),
                         'Confidence_New': sentiment.get('confidence', ''),
                         'Reasoning_New': sentiment.get('reasoning', '')
                     })
                 else:
                     result.update({
                         'Sentiment_New': 'Gagal analisis',
                         'Confidence_New': '',
                         'Reasoning_New': 'Error dalam analisis AI'
                     })
             else:
                 result.update({
                     'Sentiment_New': 'Artikel tidak dapat dibuka',
                     'Confidence_New': '',
                     'Reasoning_New': 'Tidak ada konten yang cukup untuk analisis'
                 })
         
         # 4. Summarize (if enabled)
         if config['enable_summarize']:
             if analysis_text and len(analysis_text.strip()) > 50:
                 summary = self.summarizer.summarize_article(
                     analysis_text, config['summarize_config']
                 )
                 
                 if summary:
                     result['Summary_New'] = summary.get('summary', '')
                 else:
                     result['Summary_New'] = 'Gagal membuat ringkasan'
             else:
                 result['Summary_New'] = 'Konten terlalu pendek untuk diringkas'
         
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
             return
         df = pd.DataFrame(results)
         success_count = len([r for r in results if r.get('Content', '') != ''])
     
     # Display summary with method statistics
     col1, col2, col3, col4 = st.columns(4)
     with col1:
         st.metric("Total Data", len(df))
     with col2:
         st.metric("Berhasil", success_count)
     with col3:
         if not is_excel_data:
             st.metric("Gagal", len(df) - success_count)
         else:
             # Show scraping method distribution for Excel data
             method_col = 'Scraping_Method_New' if 'Scraping_Method_New' in df.columns else 'Scraping_Method'
             if method_col in df.columns:
                 newspaper_count = len(df[df[method_col] == 'newspaper3k'])
                 st.metric("Newspaper3k", newspaper_count)
     with col4:
         if config.get('enable_summarize'):
             summary_cols = [col for col in df.columns if 'summary' in col.lower()]
             if summary_cols:
                 summary_count = len(df[df[summary_cols[0]].str.len() > 10])
                 st.metric("Summary Berhasil", summary_count)
         else:
             # Show requests method count
             method_col = 'Scraping_Method_New' if 'Scraping_Method_New' in df.columns else 'Scraping_Method'
             if method_col in df.columns:
                 requests_count = len(df[df[method_col].str.contains('requests', na=False)])
                 if requests_count > 0:
                     st.metric("Requests Fallback", requests_count)
     
     # Show method distribution
     method_col = 'Scraping_Method_New' if 'Scraping_Method_New' in df.columns else 'Scraping_Method'
     if method_col in df.columns and config.get('enable_scraping'):
         method_counts = df[method_col].value_counts()
         if len(method_counts) > 0:
             method_info = []
             for method, count in method_counts.items():
                 method_info.append(f"{method.title()}: {count}")
             st.info(f"📊 **Metode Scraping:** {' | '.join(method_info)}")
     
     # Display enabled features summary
     enabled_features = []
     if config.get('enable_scraping'):
         enabled_features.append("📄 Full Teks")
     if config.get('enable_sentiment'):
         enabled_features.append("😊 Sentimen")
     if config.get('enable_journalist'):
         enabled_features.append("👤 Jurnalis")
     if config.get('enable_summarize'):
         enabled_features.append("📝 Summarize")
     
     st.info(f"**Fungsi yang digunakan:** {' | '.join(enabled_features)}")
     
     # Export section - Simple and direct
     if success_count > 0:
         st.subheader("📤 Export Data")
         
         # Create export dataframe with all columns
         export_df = df.copy()
         
         # Show info about what will be exported
         st.info(f"💡 File Excel akan berisi **{len(export_df.columns)} kolom** dan **{len(export_df)} baris** data lengkap.")
         
         # Show column preview
         with st.expander("📋 Preview Kolom yang Akan Diexport"):
             col_preview1, col_preview2 = st.columns(2)
             
             # Separate original and new columns for display
             original_columns = [col for col in df.columns if not col.endswith('_New')]
             new_columns = [col for col in df.columns if col.endswith('_New')]
             
             with col_preview1:
                 if original_columns:
                     st.write("**📁 Kolom Asli:**")
                     for i, col in enumerate(original_columns, 1):
                         st.write(f"{i}. {col}")
             
             with col_preview2:
                 if new_columns:
                     st.write("**🆕 Kolom Hasil Analisis:**")
                     for i, col in enumerate(new_columns, 1):
                         st.write(f"{i}. {col}")
         
         # Create Excel file
         excel_buffer = BytesIO()
         export_df.to_excel(excel_buffer, index=False, engine='openpyxl')
         excel_buffer.seek(0)
         
         # Generate filename
         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
         data_type = "excel" if is_excel_data else "manual"
         features_suffix = "_".join([
             "fullteks" if config.get('enable_scraping') else "",
             "sentiment" if config.get('enable_sentiment') else "",
             "journalist" if config.get('enable_journalist') else "",
             "summarize" if config.get('enable_summarize') else ""
         ]).strip("_")
         
         filename = f"news_analysis_{data_type}_{features_suffix}_{timestamp}.xlsx"
         
         # Download button
         st.download_button(
             label="📥 Download Excel Lengkap",
             data=excel_buffer.getvalue(),
             file_name=filename,
             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             use_container_width=True
         )
     
     # Display results table with truncated content
     st.subheader("📋 Preview Hasil")
     
     # Create display dataframe with truncated content
     df_display = df.copy()
     text_columns = ['Content', 'Content_New', 'Summary', 'Summary_New', 'Reasoning', 'Reasoning_New']
     
     for col in text_columns:
         if col in df_display.columns:
             df_display[col] = df_display[col].astype(str).apply(
                 lambda x: x[:100] + "..." if len(str(x)) > 100 else x
             )
     
     st.dataframe(df_display, use_container_width=True)
     st.caption("💡 Tabel di atas menampilkan preview dengan teks terpotong. File Excel yang didownload berisi data lengkap.")
 
 def validate_configuration(self, config: Dict, urls: List[str], uploaded_file=None) -> List[str]:
     warnings = []
     
     if not any([config['enable_scraping'], config['enable_sentiment'], config['enable_journalist'], config['enable_summarize']]):
         warnings.append("⚠️ Pilih minimal satu fungsi untuk digunakan")
     
     if not GEMINI_API_KEY and (config['enable_sentiment'] or config['enable_summarize']):
         features = []
         if config['enable_sentiment']:
             features.append("analisis sentimen")
         if config['enable_summarize']:
             features.append("summarize")
         warnings.append(f"⚠️ API Key Gemini belum dikonfigurasi untuk {' dan '.join(features)}")
     
     if config['enable_sentiment']:
         if not config['sentiment_context']:
             warnings.append("⚠️ Konteks sentimen diperlukan untuk analisis sentimen")
     
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
                 with st.expander("👀 Preview Data"):
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
