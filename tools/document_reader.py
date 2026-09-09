"""
tools/document_reader.py
------------------------
Role: Tools for reading and parsing contents of local documents (TXT, PDF, DOCX).
extract_text() is also reused by tools/semantic_search.py for indexing.
"""
from pathlib import Path
from langchain_core.tools import tool

from tools._safety import check_path_allowed

SUPPORTED_TEXT_EXTENSIONS = (".txt", ".md", ".csv", ".log", ".json", ".py", ".js", ".ts")
SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS + (".pdf", ".docx")


def extract_text(path: Path) -> str:
    """
    Extracts text content from a local file (TXT-like, PDF, or DOCX).
    Returns the text, or an "Error: ..." string on failure — callers should
    treat a leading "Error:" as extraction having failed rather than raising,
    so batch operations (like indexing) can skip a bad file and continue.
    """
    if not path.exists() or not path.is_file():
        return f"Error: '{path}' does not exist."

    ext = path.suffix.lower()

    if ext in SUPPORTED_TEXT_EXTENSIONS:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return "Error: 'pypdf' is required to read PDFs. Install it with: pip install pypdf"

        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip() or "Error: No extractable text found in PDF (it may be scanned/image-based)."

    elif ext == ".docx":
        try:
            import docx
        except ImportError:
            return "Error: 'python-docx' is required to read DOCX files. Install it with: pip install python-docx"

        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs)

    else:
        return f"Error: Unsupported document format '{ext}'."


@tool
def read_document(file_path: str) -> str:
    """Reads the text content from a local document (TXT, PDF, or DOCX)."""
    try:
        path = Path(file_path).expanduser().resolve()
        sandbox_error = check_path_allowed(path)
        if sandbox_error:
            return sandbox_error
        return extract_text(path)
    except Exception as e:
        return f"Error reading document: {str(e)}"

document_reader_tools = [read_document]
