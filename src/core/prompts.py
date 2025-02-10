import yaml

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Prompts:
    SP_markdown_sections_and_parts: str
    USER_markdown_sections_and_parts: str
    SP_summarize_section_and_parts: str
    USER_summarize_section_and_parts: str


def load_prompts(base_dir: Path):
    prompts_file = base_dir.joinpath("assets").joinpath("system_prompts.yaml")
    assert prompts_file.is_file(), f"prompts file {prompts_file} does not exist"
    prompts_dict = yaml.safe_load(prompts_file.read_text())

    return Prompts(
        SP_markdown_sections_and_parts=prompts_dict['SP_markdown_sections_and_parts'],
        USER_markdown_sections_and_parts=prompts_dict['USER_markdown_sections_and_parts'],
        SP_summarize_section_and_parts=prompts_dict['SP_summarize_section_and_parts'],
        USER_summarize_section_and_parts=prompts_dict['USER_summarize_section_and_parts']
    )
