from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator, List


@dataclass
class PDFError:
    text: str
    recoverable: bool


@dataclass
class PDFPageData:
    b64_data: str
    page_num: int
    parent_path: Path


@dataclass
class PDFPageDataStep1:
    sections: List[int] = field(default_factory=list)
    parts: List[str] = field(default_factory=list)
    attempts_left: int = 3
    success: bool = False


class PDFBase:
    def __init__(self):
        self.errors: List[PDFError] = []

    def has_unrecoverable_errors(self) -> bool:
        return any([e for e in self.errors if not e.recoverable])


class PDFPage(PDFBase):
    def __init__(self):
        super().__init__()
        self.data: Optional[PDFPageData] = None
        self.prev: Optional[PDFPage] = None
        self.next: Optional[PDFPage] = None
        self.data_step1 = PDFPageDataStep1()


@dataclass
class PDFDocumentDataItemStep2Part:
    part_name: str
    part_summary: str


@dataclass
class PDFDocumentDataItemStep2:
    section: int
    section_summary: str
    parts: List[PDFDocumentDataItemStep2Part] = field(default_factory=list)


class PDFDocument(PDFBase):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.pages_cnt = 0
        self.data_step2: List[PDFDocumentDataItemStep2] = []
        self.__head: Optional[PDFPage] = None

    def insert_page(self, page: PDFPage) -> None:
        self.pages_cnt += 1

        if not self.__head:
            self.__head = page
            return

        last = self.__head
        while last.next:
            last = last.next

        page.prev = last
        last.next = page

    def __iter__(self) -> Iterator[PDFPage]:
        current = self.__head
        while current:
            yield current
            current = current.next

    def step1_done(self) -> bool:
        return all([page.data_step1.success or page.data_step1.attempts_left == 0 for page in self])

    def step2_done(self) -> bool:
        all_sections = {p for page in self for p in page.data_step1.sections}
        processed_sections = {item.section for item in self.data_step2}
        return len(all_sections & processed_sections) == len(all_sections)
