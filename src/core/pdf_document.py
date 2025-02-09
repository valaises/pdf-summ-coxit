from dataclasses import dataclass
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


class PDFDocument(PDFBase):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.pages_cnt = 0
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
