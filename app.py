import streamlit as st
from pathlib import Path
from src.organizer import scan_files, propose_plan, apply_plan, undo_last_run
from src.llm import check_ollama, summarize_text, classify_file
from src.documents import extract_text, summarize_document
from src.settings import DATA_DIR, MAX_FILE_MB, DEFAULT_MODEL

st.set_page_config(page_title="SlothDesk", page_icon="🦥", layout="wide")
st.markdown("""
<style>
/* Quiet Studio: soft graphite surfaces, restrained teal, and readable contrast. */
:root {
  color-scheme: dark;
  --studio-bg: #131518;
  --studio-panel: #1c2024;
  --studio-raised: #24292d;
  --studio-border: #30363b;
  --studio-text: #e2e5e8;
  --studio-muted: #a0a8ad;
  --studio-teal: #83aaa2;
  --studio-teal-strong: #6c988f;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
  background: var(--studio-bg);
  color: var(--studio-text);
}
[data-testid="stAppViewContainer"] {background: var(--studio-bg);}
[data-testid="stHeader"] {background: rgba(19,21,24,.92);}
.block-container {max-width: 1360px; padding: 2.5rem 2.5rem 3.5rem;}
[data-testid="stSidebar"] {background: #171a1e; border-right: 1px solid var(--studio-border);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color: var(--studio-muted);}
.hero {
  padding: 2rem 2.1rem;
  border: 1px solid var(--studio-border);
  border-radius: 14px;
  background: var(--studio-panel);
}
.hero h1 {margin:0; color:var(--studio-text); letter-spacing:-.035em; font-size:2.5rem;}
.hero p {margin:.65rem 0 0 0; color:var(--studio-muted); font-size:1.08rem;}
.hero .privacy {margin-top:1.15rem; color:#b5c0bd; font-size:.92rem;}
.small-note {color:var(--studio-muted);font-size:.9rem;}
.section-intro {max-width:760px; color:var(--studio-muted); margin-bottom:1.25rem;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px; border-color:var(--studio-border); background:var(--studio-panel);}
[data-testid="stCaptionContainer"] {color: var(--studio-muted);}
[data-testid="stTabs"] [role="tablist"] {column-gap:1.15rem; row-gap:.4rem; border-bottom:1px solid var(--studio-border);}
[data-testid="stTabs"] button[role="tab"] {color:var(--studio-muted); border-radius:8px 8px 0 0; padding:.65rem .35rem;}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color:var(--studio-teal); border-bottom-color:var(--studio-teal);
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
  background:var(--studio-raised); color:var(--studio-text);
  border-color:var(--studio-border); border-radius:8px;
}
[data-testid="stCheckbox"] label p {color:var(--studio-text);}
[data-testid="stFileUploader"] section {background:var(--studio-panel); border-color:var(--studio-border);}
[data-testid="stDataFrame"] {border:1px solid var(--studio-border); border-radius:9px; overflow:hidden;}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
  border-radius:8px; transition:background-color .15s ease, border-color .15s ease;
}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stDownloadButton"] button[kind="primary"] {
  background:var(--studio-teal-strong); color:#101817; border:1px solid var(--studio-teal-strong);
  font-weight:600;
}
[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stDownloadButton"] button[kind="primary"]:hover {
  background:var(--studio-teal); border-color:var(--studio-teal);
}
[data-testid="stAlert"] {border-radius:8px;}
hr {border-color:var(--studio-border);}
@media (max-width: 700px) {
  .block-container {padding:1.2rem 1rem 2.2rem;}
  .hero {padding:1.25rem 1.2rem;}
  .hero h1 {font-size:2rem;}
}
</style>
""", unsafe_allow_html=True)

st.markdown('''
<div class="hero">
  <h1>🦥 SlothDesk</h1>
  <p>Less time sorting files. More time for everything else.</p>
  <div class="privacy">Private by design &nbsp;·&nbsp; Files stay on this computer &nbsp;·&nbsp; AI runs locally</div>
</div>
''', unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value=DEFAULT_MODEL, help="Default: Gemma 3 4B. Install it with `ollama pull gemma3:4b`.")
    status = check_ollama(model)
    if status["ok"]:
        st.success(f"Model ready · {model}")
    else:
        st.warning("Local model not ready")
        st.caption(status["message"])
    st.divider()
    st.markdown("**Safe by default**")
    st.write("• Preview changes first")
    st.write("• No permanent deletion")
    st.write("• Undo the latest organization run")

tabs = st.tabs(["Organize files", "Summarize a document", "AI helper", "About"])

with tabs[0]:
    st.subheader("Organize your files")
    st.write("Choose a folder, scan its contents, then review every proposed destination before anything moves.")
    with st.container(border=True):
        folder = st.text_input("Folder path", value=str(Path.home() / "Downloads"))
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            recursive = st.checkbox("Include subfolders", value=False)
        with col2:
            use_ai = st.checkbox("Classify unknown types with AI", value=False)
        with col3:
            scan_clicked = st.button("Scan folder", type="primary")
    if scan_clicked:
        p = Path(folder).expanduser()
        if not p.exists() or not p.is_dir():
            st.error("That folder does not exist or is not a directory.")
        else:
            try:
                items = scan_files(p, recursive=recursive)
                plan = propose_plan(items, model=model if use_ai else None)
                st.session_state["slothdesk_plan"] = plan
                st.session_state["slothdesk_folder"] = str(p)
                st.session_state["slothdesk_recursive"] = recursive
                st.success(f"Prepared a preview for {len(plan)} file(s). Nothing has been moved.")
            except Exception as e:
                st.error(f"Could not scan folder: {e}")

    plan = st.session_state.get("slothdesk_plan")
    if plan is not None:
        st.markdown(f"#### Review plan · {len(plan)} file(s)")
        st.caption("Hidden files and folders are skipped. Existing destination names will not be overwritten. Scroll the table to review the full plan.")
        st.dataframe(
            [{"File": x["name"], "Suggested folder": x["category"], "Destination preview": x["destination"], "Reason": x["reason"]} for x in plan],
            use_container_width=True, hide_index=True, height=460
        )
        if plan:
            confirm = st.checkbox("I reviewed this plan and want to move these files.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Apply organization", disabled=not confirm, type="primary"):
                    try:
                        result = apply_plan(st.session_state["slothdesk_folder"], plan)
                        st.session_state["slothdesk_last_run"] = result
                        st.session_state.pop("slothdesk_plan", None)
                        st.success(f"Moved {len(result['moves'])} file(s). A manifest was saved for undo.")
                    except Exception as e:
                        st.error(f"Organization stopped safely: {e}")
            with c2:
                if st.button("Discard preview"):
                    st.session_state.pop("slothdesk_plan", None)
                    st.rerun()
        else:
            st.info("No files found to organize.")
    if st.button("Undo latest organization run"):
        try:
            root = st.session_state.get("slothdesk_folder", folder)
            undone = undo_last_run(root)
            st.success(f"Restored {undone} file(s) where possible.")
        except Exception as e:
            st.error(str(e))

with tabs[1]:
    st.subheader("Summarize a document")
    st.markdown('<p class="section-intro">Get a grounded summary from a text-based PDF, TXT, or Markdown file. The document is processed locally by Ollama.</p>', unsafe_allow_html=True)
    upload_col, info_col = st.columns([1.7, 1], gap="large")
    with upload_col:
        with st.container(border=True):
            uploaded = st.file_uploader("Choose a document", type=["pdf", "txt", "md"], key="doc_upload", help=f"Maximum file size: {MAX_FILE_MB} MB")
            if uploaded:
                st.caption(f"{uploaded.name} · {uploaded.size / 1024:.0f} KB")
    with info_col:
        with st.container(border=True):
            st.markdown("### Local summary")
            st.caption("Current Ollama model")
            st.code(model, language=None)
            st.markdown(f"**Accepted files**\n\nPDF · TXT · Markdown\n\n**File limit**\n\n{MAX_FILE_MB} MB")
            st.caption("Long documents or the model’s first run can take a few minutes.")
    if uploaded:
        if uploaded.size > MAX_FILE_MB * 1024 * 1024:
            st.error(f"This file is {uploaded.size / (1024 * 1024):.1f} MB. The limit is {MAX_FILE_MB} MB.")
        else:
            st.divider()
            summarize_clicked = st.button("Summarize document", type="primary")
            if summarize_clicked:
                try:
                    text = extract_text(uploaded.name, uploaded.getvalue())
                    if not text.strip():
                        st.error("No extractable text found. Scanned PDFs need OCR, which is not included yet.")
                    else:
                        with st.spinner("Summarizing locally. The first run or a long document may take a few minutes..."):
                            summary = summarize_document(text, model=model)
                        st.divider()
                        with st.container(border=True):
                            st.markdown("### Summary")
                            st.markdown(summary)
                        st.download_button("Download summary", summary, file_name=Path(uploaded.name).stem + "_summary.md")
                except Exception as e:
                    st.error(f"Could not summarize this document: {e}")

with tabs[2]:
    st.subheader("Ask your local AI helper")
    st.write("Use this for small, non-destructive tasks such as drafting a checklist or summarizing pasted text.")
    task = st.text_area("What would you like help with?", placeholder="Turn these meeting notes into a checklist...")
    if st.button("Generate response", type="primary"):
        if not task.strip():
            st.warning("Enter a task first.")
        else:
            with st.spinner("Running on your local model..."):
                response = summarize_text(task, model=model, system="You are SlothDesk, a careful productivity assistant. Be concise, practical, and never claim to have performed actions you did not perform.")
            st.markdown(response)

with tabs[3]:
    st.subheader("What SlothDesk does")
    st.markdown("""
- **File organization:** scans a selected folder and previews moves by file type before acting.
- **Document summaries:** extracts text from PDFs and text files, then summarizes with a local model.
- **Local AI helper:** turns pasted text into concise plans and checklists.
- **Undo:** records a manifest for the latest organization run and attempts to restore moved files.

### Open innovation
SlothDesk uses open-source Python tools and a locally run model through Ollama. After setup and model download, the core AI flow can work without an internet connection. Users can inspect, adapt, and extend the project rather than depending on a closed cloud API.

### Current limitations
- Scanned PDFs and OCR are not supported.
- File classification is rule-based by default; optional AI classification may be slower.
- Always review the preview. Undo is best-effort if files have since been changed or moved.
- Model weights and dependencies have their own licenses; verify each license before redistribution.
""")
    st.caption("Hacktoberfest / International Sloth Day project • Build less busywork, keep more control.")
