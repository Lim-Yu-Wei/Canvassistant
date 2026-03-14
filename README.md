# Canvassistant: Canvas to Obsidian & Telegram

Transform your Canvas course materials into a structured, linked knowledge base in Obsidian, with hourly Telegram updates.

## 🚀 The Workflow
1. **Initial Ingest**: Download all historical materials and generate "Claude-style" Obsidian notes.
2. **Maintenance**: An hourly GitHub Action polls Canvas for new PDFs, announcements, and assignments.
3. **Connect**: Use the Obsidian MCP server to chat with your vault using an LLM.

---

## 🛠️ Step 1: Initial Setup (Local)
This step downloads everything you currently have on Canvas and builds your initial Obsidian vault.

1. **Clone your repository**:
   ```bash
   git clone <your-repo-url>
   cd Canvassistant
   pip install -r requirements.txt
   ```
2. **Configure `.env`**:
   Copy `.env.example` to `.env` and fill in your:
   - `CANVAS_TOKEN` ([Guide to getting it](https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89))
   - `OPENAI_API_KEY`
   - `OBSIDIAN_API_KEY` (From the [Local REST API plugin](https://github.com/codemirror/obsidian-local-rest-api))

3. **Run the Ingest**:
   ```bash
   python scripts/initial_ingest.py
   ```
   *Your notes will be saved to the `vault/` folder and synced to your running Obsidian instance.*

---

---

## 🤖 Step 2: Hourly Automation (GitHub Actions)
Keep your vault updated automatically without keeping your computer on.

1. **Fork this repository** to your private GitHub account.
2. **Setup Telegram Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram.
   - Send `/newbot`, follow the prompts, and save the **API Token**.
   - Start a chat with your new bot and send a message.
   - Message [@userinfobot](https://t.me/userinfobot) to get your **Chat ID**.
3. **Setup GitHub Secrets**: 
   Go to your fork's `Settings > Secrets and Variables > Actions` and add:
   - `CANVAS_BASE_URL` (e.g., `https://canvas.nus.edu.sg`)
   - `CANVAS_TOKEN`
   - `OPENAI_API_KEY`
   - `TELEGRAM_BOT_TOKEN` (The one from BotFather)
   - `TELEGRAM_CHAT_ID` (The one from userinfobot)
   - `SUPABASE_URL`, `SUPABASE_KEY` (Used to track seen files)
4. **Enable the Workflow**: Go to the `Actions` tab and enable the "Daily Canvas Pipeline".

---

## 🧠 Step 3: Speak to your Vault (LLM + MCP)
Once your notes are in Obsidian, you can use an LLM to speak to them.

1. Install the [Obsidian MCP Server](https://github.com/michaelfromyork/obsidian-mcp).
2. Configure it to point to your `vault/` directory.
3. In Claude Desktop or Antigravity, add the MCP server.
4. **Ask things like**: *"What were the key takeaways from last week's CG2111A lecture?"* or *"Summarize my upcoming assignments due this week."*

---

## 🧩 Telegram Features
- **New Materials**: Receive the PDF + a concise summary immediately.
- **Announcements**: Full text push for course updates.
- **Daily Digest**: Every morning at 8 AM, receive a to-do list of all assignments due in the next 7 days.

---

## ⚖️ License
MIT License - Fee free to use and adapt for your own studies!
