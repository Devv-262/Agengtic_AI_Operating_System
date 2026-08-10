"""
tools/document_reader.py
------------------------
Role: Tools for reading and parsing contents of local documents (TXT, PDF, DOCX).
"""
import os
from pathlib import Path
from langchain_core.tools import tool

@tool
def read_document(file_path: str) -> str:
    """Reads the text content from a local document (TXT, PDF, DOCX)."""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return f"Error: Document '{path}' does not exist."
            
        ext = path.suffix.lower()
        
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == '.pdf':
            # Note: Requires PyPDF2, pdfplumber, or PyMuPDF in a real implementation.
            # This is a placeholder for the actual extraction logic.
            return f"[Simulated PDF Extraction for {path.name}]\n" \
                   f"This would contain the extracted text of the PDF."
                   
        elif ext == '.docx':
            # Note: Requires python-docx in a real implementation.
            return f"[Simulated DOCX Extraction for {path.name}]\n" \
                   f"This would contain the extracted text of the Word document."
                   
        else:
            return f"Error: Unsupported document format '{ext}'."
            
    except Exception as e:
        return f"Error reading document: {str(e)}"

document_reader_tools = [read_document]
