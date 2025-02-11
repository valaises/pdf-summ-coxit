def convert_output_format(input_data):
    output = {
        "file_name": input_data["file_name"],
        "sections": []
    }

    for section_idx, section in enumerate(input_data["sections"]):
        section_pages = [
            p["page_num"] for p in input_data["pages"]
            if section in p["sections"]
        ]

        if section_pages:
            section_entry = {
                "section": section,
                "page_start": min(section_pages),
                "page_end": max(section_pages)
            }
            output["sections"].append(section_entry)

    return output
