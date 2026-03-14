import os
import json
import logging
import requests
import pdfplumber
from pathlib import Path
from concurrent import futures
from typing import List, Dict, Set
from openai import OpenAI
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent / ".env")

# Constants from environment
CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OBSIDIAN_API_KEY = os.getenv("OBSIDIAN_API_KEY") # Optional for local setup
OBSIDIAN_BASE_URL = os.getenv("OBSIDIAN_BASE_URL", "https://127.0.0.1:27124")
DATA_DIR = Path("data")
VAULT_DIR = Path("vault")

client = OpenAI(api_key=OPENAI_API_KEY)

class InitialIngestOrchestrator:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
        self.obsidian_headers = {
            "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
            "Content-Type": "text/markdown"
        }
        self.vault_topics: Set[str] = set()
        self.processed_log_path = Path("processed_files.json")
        self.processed_files = self._load_processed_log()

    def download_all_canvas_pdfs(self):
        """Downloads every PDF from all active courses for the initial sync."""
        logger.info("Starting full Canvas PDF download...")
        courses_url = f"{CANVAS_BASE_URL}/api/v1/courses"
        params = {"enrollment_state": "active", "per_page": 100}
        
        try:
            resp = requests.get(courses_url, headers=self.headers, params=params)
            resp.raise_for_status()
            courses = resp.json()
            
            for course in courses:
                course_id = course.get("id")
                course_name = course.get("name", "Unknown").replace("/", "-")
                if not course_id: continue
                
                logger.info(f"Targeting Course: {course_name}")
                files_url = f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}/files"
                f_params = {"per_page": 100}
                
                f_resp = requests.get(files_url, headers=self.headers, params=f_params)
                if f_resp.status_code == 403: continue
                f_resp.raise_for_status()
                files = f_resp.json()
                
                for f_info in files:
                    if f_info.get("filename", "").lower().endswith(".pdf"):
                        dest_dir = DATA_DIR / course_name
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_path = dest_dir / f_info["filename"]
                        
                        if dest_path.exists(): continue
                        
                        logger.info(f"Downloading {f_info['filename']}...")
                        with requests.get(f_info["url"], headers=self.headers, stream=True) as r:
                            with open(dest_path, 'wb') as f:
                                for chunk in r.iter_content(8192): f.write(chunk)
        except Exception as e:
            logger.error(f"Canvas download failed: {e}")

    def _load_processed_log(self) -> Dict:
        if self.processed_log_path.exists():
            with open(self.processed_log_path, 'r') as f:
                return json.load(f)
        return {"processed": []}

    def _save_processed_log(self):
        with open(self.processed_log_path, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def fetch_vault_map(self):
        """Build a map of existing note titles to enable dense linking."""
        logger.info("Mapping Obsidian vault topics...")
        try:
            # We'll crawl the main directories we know exist
            folders = ["CG2111A", "CS2040C", "CS1231", "MA1508E", "DTK1234"]
            for folder in folders:
                resp = requests.get(f"{OBSIDIAN_BASE_URL}/vault/{folder}/", headers=self.headers, verify=False)
                if resp.status_code == 200:
                    files = resp.json().get("files", [])
                    for f in files:
                        if f.endswith(".md"):
                            topic = f.split("/")[-1].replace(".md", "")
                            self.vault_topics.add(topic)
                else:
                    logger.warning(f"Could not map folder {folder}: {resp.status_code}")
            logger.info(f"Vault map built with {len(self.vault_topics)} topics.")
        except Exception as e:
            logger.error(f"Failed to fetch vault map: {e}")

    def extract_text(self, pdf_path: Path) -> str:
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    content = page.extract_text()
                    if content:
                        text += content + "\n"
        except Exception as e:
            logger.error(f"Text extraction failed for {pdf_path}: {e}")
        return text

    def generate_note(self, text: str, filename: str, module_name: str) -> str:
        """Generate a Claude-style note using GPT-4o-mini."""
        logger.info(f"Generating Claude-style note for {filename}...")
        
        # Build a hint for linking based on vault topics
        topics_hint = ", ".join(list(self.vault_topics)[:50]) # Sample for context
        
        prompt = f"""Target Module: {module_name}
        Original File: {filename}
        
        Task: Convert the following lecture material into a premium, highly structured "Claude-style" Obsidian note.
        
        Strict Formatting Rules:
        1. Use YAML frontmatter with tags: [{module_name}, lecture-notes, academic].
        2. # Title: Clear, descriptive heading.
        3. ## Overview: A high-level executive summary (3-4 sentences).
        4. ## Key Concepts & Definitions: Use [[wikilinks]] for all technical terms. 
           - Existing topics to prioritize linking if relevant: {topics_hint}
        5. ## Detailed Technical Breakdown: Use subheadings, bullet points, and tables for clarity.
        6. ## Implementation/Examples (if applicable): Use triple-backtick code blocks.
        7. > [!note] / [!important] / [!warning]: Use at least 2 relevant callouts.
        8. ## Related: Link to other [[ModuleIndex]] or conceptual neighbors.

        Content:
        {text[:15000]} # Truncate to stay within context limits
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert academic tutor that writes beautifully structured Obsidian notes. IMPORTANT: Output ONLY the raw markdown. Do NOT wrap the entire response in triple backticks (```markdown)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            # Handle cases where the LLM still wraps in backticks
            if content.startswith("```markdown"):
                content = content.replace("```markdown", "", 1)
            if content.startswith("```"):
                content = content.replace("```", "", 1)
            if content.endswith("```"):
                content = content[::-1].replace("```"[::-1], "", 1)[::-1]
            
            return content.strip()
        except Exception as e:
            logger.error(f"GPT summarization failed: {e}")
            return ""

    def upload_to_obsidian(self, content: str, module_folder: str, filename: str):
        stem = Path(filename).stem
        # Ensure module folder names are consistent with Obsidian structure
        clean_folder = module_folder.split(" ")[0].upper() # e.g. "CG2111A"
        
        # 1. Save locally to /vault directory (for Git sync)
        local_path = VAULT_DIR / clean_folder / f"{stem}.md"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content, encoding="utf-8")
        logger.info(f"Saved locally: {local_path}")

        # 2. Try to sync to running Obsidian instance via REST API (optional)
        if OBSIDIAN_API_KEY:
            url = f"{OBSIDIAN_BASE_URL}/vault/{clean_folder}/{stem}.md"
            try:
                resp = requests.put(url, headers=self.obsidian_headers, data=content.encode('utf-8'), verify=False)
                if resp.status_code in [200, 201, 204]:
                    logger.info(f"Successfully synced to Obsidian API.")
                    return True
            except:
                logger.warning("Obsidian API not reachable. Note saved locally only.")
        return True

    def process_file(self, pdf_path: Path):
        file_key = str(pdf_path)
        if file_key in self.processed_files["processed"]:
            logger.info(f"Skipping already processed file: {pdf_path.name}")
            return

        full_module_name = pdf_path.parent.name
        module_code = full_module_name.split(" ")[0].upper() # Clean tag, e.g. "CG2111A"
        
        text = self.extract_text(pdf_path)
        if not text.strip():
            logger.warning(f"No text extracted from {pdf_path.name}. Skipping.")
            return

        note_content = self.generate_note(text, pdf_path.name, module_code)
        if note_content:
            if self.upload_to_obsidian(note_content, full_module_name, pdf_path.name):
                self.processed_files["processed"].append(file_key)
                self._save_processed_log()

    def run(self, max_workers=5):
        # 1. Download everything first
        self.download_all_canvas_pdfs()
        
        # 2. Map existing vault for linking
        if OBSIDIAN_API_KEY:
            self.fetch_vault_map()
        
        # 3. Process each PDF
        pdf_files = list(DATA_DIR.rglob("*.pdf"))
        unprocessed_pdf_files = [f for f in pdf_files if str(f) not in self.processed_files["processed"]]
        logger.info(f"Processing {len(unprocessed_pdf_files)} PDFs...")

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.process_file, unprocessed_pdf_files)

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    orchestrator = InitialIngestOrchestrator()
    orchestrator.run(limit = 2)
