import json

from pathlib import Path
from termcolor import colored
from queue import Queue

from utils import convert_output_format
from my_watchdog import spawn_watchdog


BASE_DIR = Path(__file__).resolve().parent.parent
EXPECTED_JSON = BASE_DIR / "expected.json"
DATASET = BASE_DIR / "dataset"
STEP1_FILE = BASE_DIR / ".step1.jsonl"


def main():
    print("test started")
    assert EXPECTED_JSON.is_file(), f"Expected JSON file not found: {EXPECTED_JSON}"
    assert DATASET.is_dir(), f"Dataset directory not found: {DATASET}"

    dataset_files = [f for f in DATASET.iterdir() if f.is_file() and f.suffix == ".pdf"]
    assert dataset_files, f"No PDF files found in the dataset directory: {DATASET}"

    expected = json.loads(EXPECTED_JSON.read_text())
    # assuming core is already up and running
    # uv run src/core/main.py -d dataset

    process_q = Queue()
    w_stop_event = spawn_watchdog(process_q, BASE_DIR)

    processed_files = []
    try:
        while True:
            _ = process_q.get()
            assert STEP1_FILE.is_file(), f"Step 1 JSON file not found: {STEP1_FILE}"
            with open(STEP1_FILE, "r") as f:
                for line in f:
                    data = json.loads(line)
                    if data["file_name"] in processed_files:
                        continue

                    print(f"Checking {data['file_name']}...")

                    expected_value = [i for i in expected if i["file_name"] == data["file_name"]][0]
                    data = convert_output_format(data)

                    if len(expected_value["sections"]) != len(data["sections"]):
                        print(colored(f"FAIL: number of section does not match: expected: {len(expected_value["sections"])}; got: {len(data["sections"])}", "red"))
                        processed_files.append(data["file_name"])
                        continue

                    sections_exp = {i["section"] for i in expected_value["sections"]}
                    sections_data = {i["section"] for i in data["sections"]}
                    if sections_exp != sections_data:
                        print(colored(f"FAIL: section does not match: expected: {sections_exp}; got: {sections_data}", "red"))
                        processed_files.append(data["file_name"])
                        continue

                    expected_value["sections"].sort(key=lambda x: x["section"])
                    data["sections"].sort(key=lambda x: x["section"])

                    for (es, ds) in zip(expected_value["sections"], data["sections"]):
                        if es["page_start"] != ds["page_start"]:
                            print(colored(f"FAIL: SECTION {es['section']} page_start does not match: expected: {es['page_start']}; got: {ds['page_start']}", "red"))
                            continue

                        if es["page_end"] != ds["page_end"]:
                            print(colored(f"FAIL: SECTION {es['section']} page_end does not match: expected: {es['page_end']}; got: {ds['page_end']}", "red"))
                            continue

                        print(colored(f"OK: SECTION {es['section']}", "green"))

                    processed_files.append(data["file_name"])

    except KeyboardInterrupt:
        print("Gracefully shutting down")
    finally:
        w_stop_event.set()


if __name__ == "__main__":
    main()