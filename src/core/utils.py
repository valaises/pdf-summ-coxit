from core.globals import STEP1_DUMP_FILE, STEP2_DUMP_FILE


def clear_dump_files():
    for file_path in [STEP1_DUMP_FILE, STEP2_DUMP_FILE]:
        if file_path.exists():
            file_path.write_text("")


def convert_output_format(input_data):
    output = {
        "file_name": input_data["file_name"],
        "sections": []
    }

    for section_idx, section in enumerate(input_data["sections"]):
        for section_n in set(p["section_n"] for p in input_data["pages"]):
            section_pages = [
                p["page_num"] for p in input_data["pages"]
                if section in p["sections"] and p["section_n"] == section_n
            ]

            if section_pages:
                section_entry = {
                    "section": section,
                    "page_start": min(section_pages),
                    "page_end": max(section_pages)
                }
                output["sections"].append(section_entry)

    return output