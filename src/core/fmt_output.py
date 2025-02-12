import json
from pathlib import Path

import pandas as pd

from core.logger import info
from globals import STEP1_DUMP_FILE, STEP2_DUMP_FILE


def format_output(target_dir: Path):
    assert STEP1_DUMP_FILE.is_file(), f"File {STEP1_DUMP_FILE} not found"
    assert STEP2_DUMP_FILE.is_file(), f"File {STEP2_DUMP_FILE} not found"

    s1_rows = []
    s2_rows = []

    with open(STEP1_DUMP_FILE, "r") as f:
        for line in f:
            data = json.loads(line)
            s1_rows.append(convert_s1_to_output(data))

    with open(STEP2_DUMP_FILE, "r") as f:
        for line in f:
            s2_rows.append(json.loads(line))

    sections_rows = []
    for item in s1_rows:
        file_name = item['file_name']
        for section in item['sections']:
            sections_rows.append({
                'file_name': file_name,
                'section': section['section'],
                'section_n': section['section_n'],
                'page_start': section['page_start'],
                'page_end': section['page_end'],
                'section_summary': ''
            })

    summaries = {
        (obj['file_name'], summary['section'], summary.get('section_n', '')): summary['section_summary']
        for obj in s2_rows
        for summary in obj['summaries']
    }

    for row in sections_rows:
        key = (row['file_name'], row['section'], row['section_n'])
        row['section_summary'] = summaries.get(key, '')

    parts_rows = []
    for obj in s2_rows:
        file_name = obj['file_name']
        for summary in obj['summaries']:
            section = summary['section']
            section_n = summary.get('section_n', '')  # Get section_n from s2_rows summary
            for part in summary['parts']:
                parts_rows.append({
                    'file_name': file_name,
                    'part': part['part_name'],
                    'section': str(section),
                    'section_n': section_n,
                    'summary': part['part_summary']
                })

    sections_df = pd.DataFrame(sections_rows).sort_values(['file_name', 'page_start'])
    parts_df = pd.DataFrame(parts_rows).sort_values(['file_name', 'section', 'section_n', 'part'])

    output_csv = target_dir / 'output.csv'
    parts_csv = target_dir / 'output_parts.csv'

    sections_df.to_csv(str(output_csv), index=False)
    info(f"Saved output to {output_csv}")
    parts_df.to_csv(str(parts_csv), index=False)
    info(f"Saved output_parts to {parts_csv}")



def convert_s1_to_output(input_data):
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
                    "section_n": section_n,
                    "page_start": min(section_pages),
                    "page_end": max(section_pages)
                }
                output["sections"].append(section_entry)

    return output
