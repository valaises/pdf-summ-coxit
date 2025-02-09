import base64
import time

from pypdf import PdfReader, PdfWriter
from io import BytesIO

from logger import warn, info
from pdf_document import PDFDocument, PDFError, PDFPage, PDFPageData


def process_pdf(doc: PDFDocument):
    time_start = time.time()

    try:
        reader = PdfReader(doc.path)
    except Exception as e:
        err = PDFError(f"Error reading PDF at path {doc.path}. Non recoverable", False)
        warn(f"{err.text}\nERROR: {e}")
        doc.errors.append(err)
        return

    for page_num in range(len(reader.pages)):
        page = PDFPage()
        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            memory_file = BytesIO()
            writer.write(memory_file)

            pdf_bytes = memory_file.getvalue()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

            page_data = PDFPageData(base64_pdf, page_num + 1, doc.path)
            page.data = page_data

            memory_file.close()

        except Exception as e:
            err = PDFError(f"Error processing page {page_num} of PDF {doc.path}. Non recoverable", False)
            warn(f"{err.text}\nERROR: {e}")
            page.errors.append(err)

        finally:
            doc.insert_page(page)

    info(
        f"Processed PDF {doc.path.name} in {time.time() - time_start:.3f}s:\n"
        f"Pages: {doc.pages_cnt}\n"
        f"Document has Unrecoverable Errors: {doc.has_unrecoverable_errors()}\n"
        f"Any Page has Unrecoverable Errors: {any([p.has_unrecoverable_errors() for p in doc])}\n"
    )
