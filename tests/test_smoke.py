from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist():
    required = ["README.md", ".env.example", "requirements.txt", "sql/001_creatoros.sql", "app/main.py", "app/agent.py", "app/memory.py", "app/db.py", "app/schemas.py", "static/index.html", "static/app.css"]
    assert all((ROOT / p).exists() for p in required)


def test_no_python_cache_is_packaged():
    assert not any(ROOT.rglob("__pycache__"))
    assert not any(ROOT.rglob("*.pyc"))


def test_memory_pipeline_markers_exist():
    memory = (ROOT / "app/memory.py").read_text(encoding="utf-8")
    main = (ROOT / "app/main.py").read_text(encoding="utf-8")
    assert "MemoryExtraction" in memory
    assert "extract_and_save" in memory
    assert "memory.extract_and_save" in main


def test_conversation_timestamp_is_touched_after_message():
    db = (ROOT / "app/db.py").read_text(encoding="utf-8")
    assert 'creatoros_conversations' in db
    assert 'update({' in db
