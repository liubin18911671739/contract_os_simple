"""
File Parser Utilities
Extract text from PDF, DOCX, and TXT files
"""
from io import BytesIO
from typing import Optional

from PyPDF2 import PdfReader
from docx import Document


def parse_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file

    Args:
        file_content: PDF file bytes

    Returns:
        Extracted text
    """
    try:
        pdf_file = BytesIO(file_content)
        reader = PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def parse_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file

    Args:
        file_content: DOCX file bytes

    Returns:
        Extracted text
    """
    try:
        docx_file = BytesIO(file_content)
        doc = Document(docx_file)

        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")


def parse_txt(file_content: bytes, encoding: str = "utf-8") -> str:
    """
    Extract text from TXT file

    Args:
        file_content: TXT file bytes
        encoding: Text encoding (default: utf-8)

    Returns:
        Text content
    """
    try:
        return file_content.decode(encoding)
    except UnicodeDecodeError:
        # Try common encodings
        for enc in ["gbk", "gb2312", "big5", "latin1"]:
            try:
                return file_content.decode(enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("Failed to decode text file with common encodings")


def parse_file(file_content: bytes, mime_type: str) -> str:
    """
    Parse file based on MIME type

    Args:
        file_content: File bytes
        mime_type: MIME type

    Returns:
        Extracted text

    Raises:
        ValueError: If unsupported file type
    """
    if mime_type == "application/pdf":
        return parse_pdf(file_content)
    elif mime_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/docx",
    ]:
        return parse_docx(file_content)
    elif mime_type in ["text/plain", "text/txt"]:
        return parse_txt(file_content)
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")
