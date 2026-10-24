import streamlit as st
from pathlib import Path
from src.organizer import scan_files, propose_plan, apply_plan, undo_last_run
from src.llm import check_ollama, summarize_text, classify_file
from src.documents import extract_text, summarize_document
from src.settings import DATA_DIR, MAX_FILE_MB, DEFAULT_MODEL

st.set_page_config(page_title="SlothDesk", page_icon="🦥", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1150px; padding-top: 1.8rem;}
.hero {padding: 1.35rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#e0f2fe,#f0fdf4);}
.hero h1 {margin:0; color:#123047;} .hero p {margin:.4rem 0 0 0;color:#334155;}
.small-note {color:#64748b;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🦥 SlothDesk</h1><p>Your local-first AI helper for the boring digital chores.</p></div>', unsafe_allow_html=True)
st.write("Organize a folder, get a quick document summary, or prepare a tidy-up plan before making changes.")
st.caption("Privacy-first design: file operations stay on your computer. AI features use your local Ollama server; nothing is intentionally sent to a hosted model API.")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value=DEFAULT_MODEL, help="Must already be installed with Ollama.")
    status = check_ollama(model)
    if status["ok"]:
        st.success(f"Local model ready: {model}")
    else:
        st.warning("Local model not ready")
        st.caption(status["message"])
    st.divider()
    st.markdown("**Safe by default**")
    st.write("• Preview changes first")
    st.write("• No permanent deletion")
    st.write("• Undo the latest organization run")

tabs = st.tabs(["📁 Organize files", "📄 Summarize a document", "🧠 AI helper", "ℹ️ About"])

with tabs[0]:
    st.subheader("Organize a folder")
    st.write("Choose a folder you own. SlothDesk will preview a plan before moving anything.")
    folder = st.text_input("Folder path", value=str(Path.home() / "Downloads"))
    col1, col2 = st.columns([1, 1])
    with col1:
        recursive = st.checkbox("Include subfolders", value=False)
    with col2:
        use_ai = st.checkbox("Use local AI to classify ambiguous files", value=False)
    if st.button("Scan and prepare plan", type="primary"):
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
        st.markdown("#### Preview")
        st.caption("Review every destination. Hidden files and folders are skipped. Existing destination names are not overwritten.")
        st.dataframe(
            [{"File": x["name"], "Suggested folder": x["category"], "Destination preview": x["destination"], "Reason": x["reason"]} for x in plan],
            use_container_width=True, hide_index=True
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
    uploaded = st.file_uploader("Upload a text-based PDF, TXT, or Markdown file", type=["pdf", "txt", "md"], key="doc_upload")
    if uploaded:
        if uploaded.size > MAX_FILE_MB * 1024 * 1024:
            st.error(f"File is too large. Limit: {MAX_FILE_MB} MB.")
        elif st.button("Summarize locally", type="primary"):
            try:
                text = extract_text(uploaded.name, uploaded.getvalue())
                if not text.strip():
                    st.error("No extractable text found. Scanned PDFs need OCR, which is not included in this MVP.")
                else:
                    with st.spinner("Asking your local model..."):
                        summary = summarize_document(text, model=model)
                    st.markdown("#### Summary")
                    st.write(summary)
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
