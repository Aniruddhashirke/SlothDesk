from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from src.llm import generate
from src.settings import DEFAULT_MODEL

def extract_text(filename, content):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {i}]\n{text}")
        return "\n\n".join(pages)
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")
    raise ValueError("Unsupported file type. Use PDF, TXT, or Markdown.")

def summarize_document(text, model=DEFAULT_MODEL):
    prompt = (
        "Summarize the following study/work document. Use headings: Overview, Key Points, "
        "Action Items (only if applicable), and Questions to Verify. Do not invent facts. "
        "If the text contains page markers like [Page 2], preserve them when useful.\n\n"
        + text[:24000]
    )
    return generate(prompt, model=model, system="You are a concise assistant. Ground your summary in the provided text.")
