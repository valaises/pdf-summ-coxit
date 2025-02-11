from core.globals import STEP1_DUMP_FILE, STEP2_DUMP_FILE


def clear_dump_files():
    for file_path in [STEP1_DUMP_FILE, STEP2_DUMP_FILE]:
        if file_path.exists():
            file_path.write_text("")
