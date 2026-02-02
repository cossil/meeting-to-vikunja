# 📝 MeetingToVikunja

**Turn messy meeting transcripts into actionable Vikunja tasks using Google Gemini AI.**

## 📖 Overview

**MeetingToVikunja** is a local Python application designed to bridge the gap between **Audio Transcripts** (from tools like Whisper, Otter.ai, etc.) and your **Task Management System** (Vikunja).

Unlike generic summarizers, this tool uses a **High-Recall Prompting Strategy** to ensure no task is left behind, regardless of how fragmented or informal the conversation was. It features a custom "Phonetic Glossary" to correct Speech-to-Text errors specific to your business domain.

### ✨ Key Features

* **🧠 High-Recall Extraction:** Optimized System Prompt designed to "dig deep" into long transcripts and extract 100% of actionable items, consolidating duplicates without losing context.
* **🗣️ Contextual "Noise" Filtering:** Aggressively filters out filler words ("né", "tipo"), personal chit-chat (lunch, weather), and STT hallucinations.
* **📚 Dynamic Phonetic Glossary:** A built-in Knowledge Base (editable via UI) to fix recurring STT errors (e.g., teaching the AI that "Rock" = "Roquelina" or "PN" = "APN").
* **📂 Multi-File Support:** Handles fragmented meetings (e.g., `part1.mp3`, `part2.mp3`) treating them as a continuous event.
* **🛡️ Local Backup:** Automatically saves a Markdown report (`.md`) of every processed meeting locally before syncing to the API.
* **👥 Smart User Mapping:** Fuzzy matching algorithms link names mentioned in the audio to real Vikunja User IDs.

## 🛠️ Installation

### Prerequisites

* Python 3.10 or higher.
* A self-hosted [Vikunja](https://vikunja.io/) instance (or cloud account).
* A [Google AI Studio](https://aistudio.google.com/) API Key.

### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/cossil/meeting-to-vikunja
cd meeting-to-vikunja

```


2. **Install dependencies:**
```bash
pip install -r requirements.txt

```


3. **Configure Environment:**
Create a `.env` file in the root directory and add your credentials:
```ini
VIKUNJA_API_URL=https://your-vikunja-instance.com/api/v1
VIKUNJA_API_TOKEN=your_vikunja_token
TARGET_PROJECT_ID=the ID # of the Project/List where tasks go
GOOGLE_API_KEY=your_google_gemini_key
LOCAL_BACKUP_PATH=./Docs

```



## 🚀 Usage

Run the application using Streamlit:

```bash
streamlit run app.py

```

### The Workflow

1. **Select Date:** Choose the actual date the meeting occurred (crucial for relative dates like "next Friday").
2. **Upload:** Drag & drop your transcript files (`.txt`, `.md`, `.csv`).
3. **Instruction (Optional):** Add specific context in the sidebar (e.g., "Ignore the discussion about the coffee machine").
4. **Review:** The AI will generate a table of tasks. You can edit titles, assignees, and priorities inline.
5. **Sync:** Click "Synchronize" to send tasks to Vikunja and save a local Markdown report.

## ⚙️ Advanced Configuration

### The Glossary (`glossary.json`)

The application creates a `glossary.json` file automatically. You can manage this via the **"📚 Dicionário de Correção"** expander in the Sidebar.

This is used to map phonetic errors to correct entities:

* **Key:** The correct term (e.g., "Hankell").
* **Values:** A list of common errors (e.g., "Rankel", "Hanquel", "Rank").

### Prompt Engineering

The core logic resides in `logic.py`. The system uses a strict JSON schema enforcement to ensure stability. If you fork this project, be careful when modifying the `GeminiService` class prompts.

## 🤝 Contributing

Contributions are welcome! If you want to add support for other Task Managers (Jira, Trello, Notion) or improve the AI logic:

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Disclaimer:** This tool relies on Generative AI. Always review the extracted tasks before syncing them to your production environment.