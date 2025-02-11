from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUMMARIZER_MODEL = "gemini-2.0-flash"
SUMMARIZER_BS = 8
STEP1_DUMP_FILE = BASE_DIR / ".step1.jsonl"
STEP2_DUMP_FILE = BASE_DIR / ".step2.jsonl"