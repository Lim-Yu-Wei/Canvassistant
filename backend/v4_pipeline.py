import os
import json
import logging
import requests
import asyncio
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Third-party libraries
import pdfplumber
from supabase import create_client, Client
from openai import OpenAI

# VERSION tracking to verify deployment in logs
VERSION = "4.0"

# Load environment variables (.env locally, Secrets in GitHub)
load_dotenv()

# Configuration (Read directly from environment variables)
CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Local directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def telegram_send_pdf(file_path, course_name):
    """Send a PDF document with a short caption to the user via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing. Could not send notification.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            files = {'document': doc}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': f"📚 *New Course Material*\nCourse: {course_name}\nFile: {file_path.name}",
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, files=files)
            if response.status_code != 200:
                logger.error(f"Telegram sendDocument failed: {response.text}")
            response.raise_for_status()
            logger.info(f"Successfully sent {file_path.name} to Telegram.")
    except Exception as e:
        logger.error(f"Failed to send Telegram document: {e}")

def telegram_send_message(message):
    """Send a text message to Telegram (up to 4096 chars)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        # Truncate if somehow exceeds 4096
        safe_msg = message[:4090]
        response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": safe_msg, "parse_mode": "Markdown"})
        if response.status_code != 200:
            logger.error(f"Telegram sendMessage failed: {response.text}")
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

def telegram_notify_error(message):
    """Send a plain text error notification to Telegram."""
    telegram_send_message(message)

class CanvasPipeline:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
        
        # Initialize Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase configuration missing.")
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Initialize OpenAI
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def is_file_seen(self, file_id):
        """Check Supabase for existing file_id."""
        response = self.supabase.table("seen_files").select("file_id").eq("file_id", str(file_id)).execute()
        return len(response.data) > 0

    def mark_file_seen(self, file_id):
        """Insert seen file_id into Supabase."""
        self.supabase.table("seen_files").insert({"file_id": str(file_id)}).execute()

    def get_active_courses(self):
        url = f"{CANVAS_BASE_URL}/api/v1/courses"
        params = {"enrollment_state": "active", "per_page": 100}
        courses = []
        while url:
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            courses.extend(resp.json())
            url = None
            link = resp.headers.get("Link", "")
            if 'rel="next"' in link:
                for part in link.split(","):
                    if 'rel="next"' in part:
                        url = part[part.index("<")+1 : part.index(">")]
                        params = {}
        return courses

    def get_course_files(self, course_id):
        """
        Fetches files for a course, filtered by creation date.
        Only returns files created in the last 48 hours.
        """
        url = f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}/files"
        # Sort by newest first so we can stop early
        params = {"per_page": 100, "sort": "created_at", "order": "desc"}
        
        # Threshold: 48 hours ago
        threshold_date = datetime.now(timezone.utc) - timedelta(hours=48)
        
        files = []
        try:
            while url:
                resp = requests.get(url, headers=self.headers, params=params)
                if resp.status_code == 403:
                    logger.warning(f"[V{VERSION}] Access to files for course {course_id} is Forbidden (403). Skipping.")
                    return []
                resp.raise_for_status()
                
                batch = resp.json()
                stop_paging = False
                
                for file_info in batch:
                    # Canvas dates are usually ISO8601 strings like "2023-01-01T12:00:00Z"
                    created_at_str = file_info.get("created_at")
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at < threshold_date:
                            logger.info(f"[V{VERSION}] Reached historical files (older than 48h). Stopping search for course {course_id}.")
                            stop_paging = True
                            break
                    files.append(file_info)
                
                if stop_paging:
                    break
                
                url = None
                link = resp.headers.get("Link", "")
                if 'rel="next"' in link:
                    for part in link.split(","):
                        if 'rel="next"' in part:
                            url = part[part.index("<")+1 : part.index(">")]
                            params = {}
            return files
        except Exception as e:
            logger.error(f"[V{VERSION}] Error fetching files for course {course_id}: {e}")
            return []

    def summarize_pdf(self, file_path):
        """
        Summarizes PDF using a Map-Reduce approach:
        1. Extract all text with pdfplumber.
        2. Chunk text (12000 chars + 1000 overlap).
        3. Summarize each chunk (Map).
        4. Combine summaries into a final report (Reduce).
        """
        try:
            logger.info(f"[V{VERSION}] Extracting text from {file_path.name}...")
            all_text = ""
            with pdfplumber.open(file_path) as pdf:
                all_text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
            
            if not all_text.strip():
                return "Could not extract text from PDF (it might be scanned or empty)."

            # Split into 12000-character chunks with 1000 overlap
            chunk_size = 12000
            overlap = 1000
            chunks = []
            start = 0
            while start < len(all_text):
                end = start + chunk_size
                chunks.append(all_text[start:end])
                start += (chunk_size - overlap)

            logger.info(f"[V{VERSION}] Split document into {len(chunks)} chunks.")

            # Map: Summarize chunks
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"[V{VERSION}] Summarizing chunk {i+1}/{len(chunks)}...")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Summarize the following section of lecture material. Focus on core concepts and technical definitions."},
                        {"role": "user", "content": chunk}
                    ]
                )
                chunk_summaries.append(response.choices[0].message.content)

            # Reduce: Combine summaries
            logger.info(f"[V{VERSION}] Reducing chunk summaries into final report...")
            combined_prompt = "\n\n".join(chunk_summaries)
            final_response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional study assistant. Combine these partial lecture summaries into one cohesive final summary. Use 5 to 8 bullet points. Highlight key definitions and potential exam topics."
                    },
                    {
                        "role": "user", 
                        "content": combined_prompt
                    }
                ]
            )
            return final_response.choices[0].message.content

        except Exception as e:
            logger.error(f"[V{VERSION}] Summarization failed for {file_path.name}: {e}")
            return f"Summarization failed: {e}"

    def process(self):
        try:
            logger.info(f"--- Starting Canvas Pipeline Version {VERSION} ---")
            courses = self.get_active_courses()
            logger.info(f"[V{VERSION}] Found {len(courses)} active courses.")

            for course in courses:
                course_id = course.get("id")
                course_name = course.get("name", f"Course_{course_id}").replace("/", "-")
                logger.info(f"[V{VERSION}] Processing course: {course_name}")

                files = self.get_course_files(course_id)
                pdf_files = [f for f in files if f.get("filename", "").lower().endswith(".pdf")]
                
                if not pdf_files:
                    continue

                for file_info in pdf_files:
                    file_id = file_info.get("id")
                    filename = file_info.get("filename")

                    if self.is_file_seen(file_id):
                        continue

                    logger.info(f"[V{VERSION}] New file discovered: {filename}")
                    
                    # 1. Download locally
                    download_url = file_info.get("url")
                    if not download_url:
                        continue
                    
                    local_path = DATA_DIR / filename
                    DATA_DIR.mkdir(exist_ok=True)
                    
                    with requests.get(download_url, headers=self.headers, stream=True) as r:
                        r.raise_for_status()
                        with open(local_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)

                    # 2. Summarize (V4 Map-Reduce)
                    summary = self.summarize_pdf(local_path)
                    
                    # 3. Notify Telegram (Split)
                    telegram_send_pdf(local_path, course_name)
                    
                    summary_msg = f"📝 *Summary ({filename})*\n\n{summary}"
                    telegram_send_message(summary_msg)

                    # 4. Clean up local file
                    local_path.unlink()
                    
                    # 5. Mark seen in Supabase
                    self.mark_file_seen(file_id)

            logger.info(f"--- Pipeline Version {VERSION} Finished Successfully ---")

        except Exception as e:
            logger.exception(f"[V{VERSION}] Pipeline execution failed.")
            telegram_notify_error(f"❌ *Canvas Pipeline V{VERSION} Error*\n\n```python\n{str(e)}\n```")

if __name__ == "__main__":
    pipeline = CanvasPipeline()
    pipeline.process()
