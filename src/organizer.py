from pathlib import Path
from datetime import datetime
import json
import shutil
import uuid

from src.llm import classify_file
from src.settings import MANIFEST_DIR

EXTENSION_MAP = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"},
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tif", ".tiff"},
    "Videos": {".mp4", ".mov", ".mkv", ".avi", ".webm"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".yml", ".yaml", ".toml"},
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
}

def category_for(path):
    ext = path.suffix.lower()
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return category, f"Extension {ext or '(none)'}"
    return "Other", "Unknown file extension"

def scan_files(folder, recursive=False):
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Folder does not exist.")
    candidates = root.rglob("*") if recursive else root.iterdir()
    items = []
    for path in candidates:
        if not path.is_file() or path.name.startswith("."):
            continue
        # Avoid scanning SlothDesk's own data if the user selected a parent folder.
        try:
            resolved = path.resolve()
            if MANIFEST_DIR in resolved.parents:
                continue
        except OSError:
            continue
        category, reason = category_for(path)
        items.append({"path": str(path), "name": path.name, "category": category, "reason": reason})
    return items

def propose_plan(items, model=None):
    plan = []
    for item in items:
        category = item["category"]
        reason = item["reason"]
        if model and category == "Other":
            try:
                category = classify_file(item["name"], model=model)
                reason = "Suggested by local AI from filename only"
            except Exception:
                category = "Other"
                reason = "AI unavailable; kept in Other"
        plan.append({
            "source": item["path"],
            "name": item["name"],
            "category": category,
            "destination": f"{category}/{item['name']}",
            "reason": reason
        })
    return plan

def _unique_destination(path):
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for i in range(1, 10000):
        candidate = path.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not find a safe non-conflicting destination.")

def apply_plan(root, plan):
    root = Path(root).expanduser().resolve()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    moves = []
    try:
        for item in plan:
            source = Path(item["source"]).resolve()
            if root not in source.parents:
                raise ValueError(f"Refusing to move a file outside the selected folder: {source}")
            if not source.exists() or not source.is_file():
                continue
            destination_dir = root / item["category"]
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = _unique_destination(destination_dir / source.name)
            shutil.move(str(source), str(destination))
            moves.append({"source": str(source), "destination": str(destination)})
    except Exception:
        # Best-effort rollback if a move fails mid-run.
        for move in reversed(moves):
            src, dst = Path(move["source"]), Path(move["destination"])
            if dst.exists() and not src.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
        raise
    manifest = {"run_id": run_id, "root": str(root), "created_at": datetime.now().isoformat(), "moves": moves}
    manifest_path = MANIFEST_DIR / f"{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (MANIFEST_DIR / "latest.json").write_text(json.dumps({"manifest": str(manifest_path)}, indent=2), encoding="utf-8")
    return manifest

def undo_last_run(root):
    root = Path(root).expanduser().resolve()
    latest_file = MANIFEST_DIR / "latest.json"
    if not latest_file.exists():
        raise FileNotFoundError("No organization manifest found yet.")
    manifest_path = Path(json.loads(latest_file.read_text(encoding="utf-8"))["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if Path(manifest["root"]).resolve() != root:
        raise ValueError("The latest organization run belongs to a different folder. Enter that original folder to undo it.")
    restored = 0
    for move in reversed(manifest["moves"]):
        source, destination = Path(move["source"]), Path(move["destination"])
        if destination.exists() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            restored += 1
    manifest_path.rename(manifest_path.with_suffix(".undone.json"))
    latest_file.unlink(missing_ok=True)
    return restored
