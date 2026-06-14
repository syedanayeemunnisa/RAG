import os
from pathlib import Path
from typing import List

import pypdf
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_path: str) -> List[str]:
    """Load a PDF file and return a list of text chunks.

    The PDF is read page‑by‑page, then each page’s text is split using a
    recursive character splitter to produce reasonably sized chunks for
    embedding (default chunk size 1000 characters with 200 character overlap).
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = pypdf.PdfReader(file_path)
    pages_text = []
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()
        if text:
            pages_text.append(text)
    # Combine pages into a single string for splitting
    full_text = "\n\n".join(pages_text)
    # Clean up surrogate characters that cannot be encoded to UTF-8 (common in PDF extraction)
    full_text = full_text.encode("utf-8", errors="ignore").decode("utf-8")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    return chunks

