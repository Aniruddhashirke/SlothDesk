# 🦥 SlothDesk

Your local-first AI helper for boring digital chores.

SlothDesk is a Streamlit app that organizes files, summarizes text-based documents, and turns pasted notes into practical checklists. AI features use a local [Ollama](https://ollama.com/) model, so your document contents are not intentionally sent to a hosted model API.

## Features

- **Preview-first file organization** — sort files into folders by type and review every proposed move before anything changes.
- **Optional local AI classification** — ask Ollama to classify files with unknown extensions using the filename only.
- **Document summaries** — summarize text-based PDF, TXT, and Markdown files.
- **AI productivity helper** — turn pasted notes or instructions into concise plans, checklists, and summaries.
- **Undo support** — save a manifest for the latest organization run and restore moved files where possible.
- **Privacy-first workflow** — file operations stay on your computer and Ollama runs locally.

## Architecture

**Main flow:** `Streamlit UI (app.py) -> Application services (src/) -> Local filesystem and Ollama API`

**File organization:** `Folder path -> Scan and classify -> Preview plan -> Confirm -> Move files -> Save undo manifest`

**Document AI:** `PDF/TXT/Markdown upload -> Text extraction -> Ollama generate endpoint -> Summary download`

**AI helper:** `Pasted text -> Prompt builder -> Local Ollama model -> Checklist, plan, or summary`

### Architecture 

```text
.
|-- app.py (Streamlit UI)
|   |-- Organize files
|   |   `-- src/organizer.py -> scan -> classify -> preview -> confirm -> local filesystem
|   |       `-- undo -> local manifest in SLOTHDESK_DATA_DIR
|   |-- Summarize document
|   |   `-- src/documents.py -> extract PDF/TXT/Markdown text -> src/llm.py
|   |-- AI helper
|   |   `-- pasted text -> src/llm.py -> local Ollama model -> checklist or plan
|   `-- Settings
|       `-- src/settings.py -> environment variables
|-- src/
|   |-- organizer.py (file scanning, planning, moving, and undo)
|   |-- documents.py (document text extraction)
|   |-- llm.py (Ollama API client and prompts)
|   `-- settings.py (application configuration)
|-- tests/ (organizer tests)
`-- Local services
    `-- Ollama at http://localhost:11434
```

The application is intentionally small and local-first:

- `app.py` owns the Streamlit interface and user confirmation steps.
- `src/organizer.py` handles scanning, category planning, safe moves, conflict resolution, and undo manifests.
- `src/documents.py` extracts text from supported document formats.
- `src/llm.py` communicates with the local Ollama server.
- `src/settings.py` centralizes environment-backed configuration.
- `tests/` covers core organizer behavior.

## Requirements

- Python 3.11 or newer
- [Ollama](https://ollama.com/) installed and running for AI features
- An Ollama model, such as `qwen2.5:3b`

Ollama is not required to scan and organize files using the built-in extension rules, but it is required for document summaries, the AI helper, and optional AI classification.

## Installation

Clone or download this repository, then open a terminal in the `SlothDesk` directory.

### Install and start Ollama

Install Ollama from [ollama.com](https://ollama.com/). If Ollama is not already running as a desktop service, start it in a separate terminal:

```bash
ollama serve
```

In another terminal, download and verify the model:

```bash
ollama pull gemma3:4b
ollama list
```

The model download requires internet access. After the model and Python dependencies are installed, SlothDesk's AI requests can run against the local Ollama server.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>.

## Configuration

SlothDesk reads configuration from environment variables. The available variables are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `gemma3:4b` | Model used for AI features |
| `MAX_FILE_MB` | `20` | Maximum document upload size |
| `SLOTHDESK_DATA_DIR` | `~/.slothdesk` | Location for undo manifests |

For example:

**PowerShell**

```powershell
$env:OLLAMA_MODEL = "gemma3:4b"
$env:MAX_FILE_MB = "30"
streamlit run app.py
```

**macOS or Linux**

```bash
export OLLAMA_MODEL="gemma3:4b"
export MAX_FILE_MB="30"
streamlit run app.py
```

The [`.env.example`](.env.example) file lists the same settings as a reference. The current application does not load `.env` files automatically, so export variables in your shell or use a launcher that loads them.

The examples above use `gemma3:4b`; run `ollama pull gemma3:4b` before starting the app if you choose that model. Otherwise, use the default `qwen2.5:3b`.

## Using the app

### Organize files

1. Enter a folder path.
2. Choose whether to include subfolders.
3. Optionally enable local AI classification for unknown file types.
4. Select **Scan and prepare plan**.
5. Review the preview and confirm the moves.
6. Use **Undo latest organization run** if you need to restore the latest run.

The organizer creates category folders such as `Documents`, `Images`, `Code`, and `Spreadsheets`. Existing names are not overwritten; conflicting files receive a numbered suffix.

Supported extension categories include:

| Category | Example extensions |
| --- | --- |
| Documents | `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`, `.tif`, `.tiff` |
| Videos | `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm` |
| Audio | `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a` |
| Archives | `.zip`, `.rar`, `.7z`, `.tar`, `.gz` |
| Code | `.py`, `.js`, `.ts`, `.html`, `.css`, `.java`, `.cpp`, `.json`, `.yml` |
| Spreadsheets | `.csv`, `.xls`, `.xlsx`, `.ods` |
| Presentations | `.ppt`, `.pptx`, `.odp` |
| Other | Unknown extensions or files without a recognized extension |

### Summarize a document

Upload a text-based PDF, TXT, or Markdown file and select **Summarize locally**. The result can be downloaded as a Markdown file.

Scanned or image-only PDFs are not supported because OCR is outside the current MVP.

### Use the AI helper

Paste notes or a small task, then ask SlothDesk to produce a summary, plan, or checklist. The helper is non-destructive and does not claim to have changed files.

## Running tests

```bash
pytest -q
```

## Troubleshooting

### `Cannot reach Ollama at localhost:11434`

Make sure Ollama is installed and running. Start it with `ollama serve`, then confirm that the server responds:

```bash
ollama list
```

### `Model is not installed`

Pull the configured model and make sure the name matches `OLLAMA_MODEL`:

```bash
ollama pull gemma3:4b
```

### PowerShell will not activate `.venv`

Run this in PowerShell for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### A PDF produces no text

The current MVP supports text-based PDFs only. Scanned or image-only PDFs require OCR, which is not included.

### A file cannot be moved

Close applications that may be using the file, check folder permissions, and retry with a disposable folder. SlothDesk stops safely if a move fails and attempts to roll back moves from the current run.

## Privacy and local data

- File scanning and organization happen on the selected local folder.
- Document text and pasted prompts are sent only to the configured Ollama server.
- Optional AI classification sends the filename, not the file contents.
- Undo manifests are stored locally under `SLOTHDESK_DATA_DIR`, which defaults to `~/.slothdesk`.
- `.env` files, virtual environments, caches, and local secrets are excluded by [`.gitignore`](.gitignore).
- Do not expose Streamlit or Ollama to the public internet without authentication and additional security controls.

## Performance notes

AI response time depends on the Ollama model, available RAM, CPU/GPU, and document size. Smaller models such as `qwen2.5:3b` are generally easier to run on CPU-only machines. Documents are limited to `MAX_FILE_MB` for upload and prompts are truncated before being sent to Ollama.

## Project structure

```text
SlothDesk/
├── app.py                 # Streamlit user interface
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
├── .env.example           # Configuration reference
├── src/
│   ├── settings.py        # Environment-backed settings
│   ├── llm.py             # Ollama client and prompts
│   ├── organizer.py       # Scan, preview, move, and undo logic
│   └── documents.py       # PDF and text extraction
└── tests/
    └── test_organizer.py  # Organizer unit tests
```

## Safety and limitations

- Always use a disposable test folder before demonstrating file organization.
- Every move is previewed and requires confirmation.
- The organizer does not permanently delete files.
- Undo is best-effort and may not restore files that were changed or moved afterward.
- The latest undo manifest is stored under `SLOTHDESK_DATA_DIR`.
- AI-generated summaries can contain mistakes; verify important information.
- Optional AI classification sends only the filename to the local Ollama server.
- Do not expose Streamlit or Ollama publicly without adding authentication and appropriate security controls.
- Check the licenses for Ollama models and dependencies before redistribution.

## Contributing

Issues and pull requests are welcome. Before opening a pull request:

1. Keep file operations preview-first and reversible where possible.
2. Add or update tests for behavior changes.
3. Run `pytest -q`.
4. Test the Streamlit workflow with a disposable folder.
5. Document any new configuration or model requirements.

## Open innovation

SlothDesk is built with open-source Python tooling and a model that runs on the user's own machine. Local inference can reduce dependence on hosted APIs and per-request costs while keeping the workflow inspectable and adaptable by the community. Hardware and electricity still have costs, and model licenses should always be reviewed before redistribution.

## Roadmap

- Add OCR support for scanned PDFs.
- Add duplicate detection and richer file rules.
- Support multiple undo histories instead of only the latest run.
- Add automated CI checks for tests and formatting.
- Improve model and hardware guidance for first-time users.

## License

SlothDesk is released under the [MIT License](LICENSE). Ollama models and third-party dependencies may have separate licenses; review them before redistribution.
