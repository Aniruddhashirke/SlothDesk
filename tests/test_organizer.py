from pathlib import Path
from src.organizer import category_for, propose_plan

def test_category_for_pdf():
    category, reason = category_for(Path("lecture.pdf"))
    assert category == "Documents"
    assert ".pdf" in reason

def test_propose_plan_destination():
    plan = propose_plan([{"path": "/tmp/notes.txt", "name": "notes.txt", "category": "Documents", "reason": "Extension .txt"}])
    assert plan[0]["destination"] == "Documents/notes.txt"
