import hashlib
import io
import re
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
import pymupdf
import docx

from app.core.config import settings


def validate_file_format_and_size(filename: str, content: bytes) -> str:
    """
    Validate uploaded file:
    1. Size check (not empty, under configurable max size e.g. 15MB).
    2. Extension check (only .pdf or .docx).
    3. Magic bytes & parser validation (prevents arbitrary file upload or spoofed extensions).
    Returns normalized extension: '.pdf' or '.docx'.
    """
    # 1. Size check
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({actual_mb:.1f} MB) exceeds the maximum allowed limit of {max_mb:.0f} MB.",
        )

    # 2. Extension check
    file_path = Path(filename or "document")
    ext = file_path.suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only {allowed_str} files are supported.",
        )

    # 3. Magic bytes and structure verification
    if ext == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. The file signature does not match PDF format.",
            )
        try:
            with pymupdf.open(stream=content, filetype="pdf") as doc:
                if len(doc) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="PDF file contains no pages.",
                    )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or unreadable PDF document: {str(e)}",
            )

    elif ext == ".docx":
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOCX file. The file signature does not match DOCX/ZIP format.",
            )
        try:
            if not zipfile.is_zipfile(io.BytesIO(content)):
                raise ValueError("Not a valid ZIP archive")
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ValueError("Missing 'word/document.xml' entry")
            # Verify python-docx can parse the document
            docx.Document(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or invalid Word (.docx) document: {str(e)}",
            )

    return ext


def _split_into_chunks(text: str, max_chars: int = 1000) -> List[str]:
    """
    Helper to break a block of text into chunks of at most max_chars without
    breaking sentences if possible.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Split by paragraphs or sentence boundaries
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks = []
    current_chunk = []
    current_len = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # If single sentence is itself huge, break by character window
        if len(part) > max_chars:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
            for k in range(0, len(part), max_chars):
                sub = part[k : k + max_chars].strip()
                if sub:
                    chunks.append(sub)
            continue

        if current_len + len(part) > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [part]
            current_len = len(part)
        else:
            current_chunk.append(part)
            current_len += len(part) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def process_pdf(
    content: bytes,
    contract_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract text page-by-page from PDF and split into chunks.
    Preserves 1-indexed page numbers.
    Rejects empty or scanned PDFs without extractable text.
    """
    doc = pymupdf.open(stream=content, filetype="pdf")
    page_count = len(doc)
    all_chunks: List[Dict[str, Any]] = []
    total_text_length = 0
    chunk_index = 0

    for page_idx in range(page_count):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_text = page.get_text("text").strip()
        total_text_length += len(page_text)

        if not page_text:
            continue

        page_chunks = _split_into_chunks(page_text, max_chars=1000)
        for chunk_text in page_chunks:
            if not chunk_text.strip():
                continue
            word_count = len(chunk_text.split())
            all_chunks.append({
                "contract_id": contract_id,
                "organization_id": organization_id,
                "chunk_index": chunk_index,
                "content": chunk_text,
                "token_count": word_count,
                "page_number": page_num,
                "embedding_metadata": {
                    "source_type": "pdf",
                    "page_number": page_num,
                    "char_count": len(chunk_text),
                    "word_count": word_count,
                },
            })
            chunk_index += 1

    # Detect empty or scanned PDFs
    if total_text_length == 0 or len(all_chunks) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "PDF contains no extractable text. Scanned or image-only documents "
                "without an embedded OCR text layer are not supported."
            ),
        )

    metadata = {
        "source_type": "pdf",
        "page_count": page_count,
        "total_characters": total_text_length,
        "total_chunks": len(all_chunks),
    }

    return all_chunks, metadata


def process_docx(
    content: bytes,
    contract_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract paragraphs and table contents from DOCX and split into chunks.
    Preserves paragraph or table references.
    Does not invent page numbers (page_number=None).
    Rejects empty documents.
    """
    doc = docx.Document(io.BytesIO(content))
    all_chunks: List[Dict[str, Any]] = []
    total_text_length = 0
    chunk_index = 0

    # 1. Collect non-empty paragraphs with index
    paragraphs_data = []
    for p_idx, p in enumerate(doc.paragraphs):
        p_text = p.text.strip()
        if p_text:
            paragraphs_data.append((p_idx + 1, p_text))
            total_text_length += len(p_text)

    # 2. Collect tables text
    tables_data = []
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            cell_texts = [c.text.strip() for c in row.cells if c.text.strip()]
            # deduplicate repeated merged cell text in a row
            unique_cells = []
            for ct in cell_texts:
                if not unique_cells or ct != unique_cells[-1]:
                    unique_cells.append(ct)
            if unique_cells:
                row_str = " | ".join(unique_cells)
                tables_data.append((f"Table {t_idx + 1}, Row {r_idx + 1}", row_str))
                total_text_length += len(row_str)

    if total_text_length == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Word (.docx) document contains no extractable text.",
        )

    # Chunk paragraphs
    current_batch: List[str] = []
    current_para_refs: List[int] = []
    current_len = 0

    for p_num, p_text in paragraphs_data:
        # If single paragraph is very long, flush batch and split paragraph
        if len(p_text) > 1000:
            if current_batch:
                chunk_str = "\n\n".join(current_batch)
                word_count = len(chunk_str.split())
                all_chunks.append({
                    "contract_id": contract_id,
                    "organization_id": organization_id,
                    "chunk_index": chunk_index,
                    "content": chunk_str,
                    "token_count": word_count,
                    "page_number": None,  # Strictly None for DOCX
                    "embedding_metadata": {
                        "source_type": "docx",
                        "reference": f"Paragraphs {current_para_refs[0]}-{current_para_refs[-1]}",
                        "paragraph_range": current_para_refs,
                        "char_count": len(chunk_str),
                        "word_count": word_count,
                    },
                })
                chunk_index += 1
                current_batch = []
                current_para_refs = []
                current_len = 0

            # Split large paragraph
            sub_chunks = _split_into_chunks(p_text, max_chars=1000)
            for sc in sub_chunks:
                word_count = len(sc.split())
                all_chunks.append({
                    "contract_id": contract_id,
                    "organization_id": organization_id,
                    "chunk_index": chunk_index,
                    "content": sc,
                    "token_count": word_count,
                    "page_number": None,
                    "embedding_metadata": {
                        "source_type": "docx",
                        "reference": f"Paragraph {p_num}",
                        "paragraph_range": [p_num],
                        "char_count": len(sc),
                        "word_count": word_count,
                    },
                })
                chunk_index += 1
            continue

        if current_len + len(p_text) > 1000 and current_batch:
            chunk_str = "\n\n".join(current_batch)
            word_count = len(chunk_str.split())
            ref = (
                f"Paragraph {current_para_refs[0]}"
                if len(current_para_refs) == 1
                else f"Paragraphs {current_para_refs[0]}-{current_para_refs[-1]}"
            )
            all_chunks.append({
                "contract_id": contract_id,
                "organization_id": organization_id,
                "chunk_index": chunk_index,
                "content": chunk_str,
                "token_count": word_count,
                "page_number": None,
                "embedding_metadata": {
                    "source_type": "docx",
                    "reference": ref,
                    "paragraph_range": current_para_refs,
                    "char_count": len(chunk_str),
                    "word_count": word_count,
                },
            })
            chunk_index += 1
            current_batch = [p_text]
            current_para_refs = [p_num]
            current_len = len(p_text)
        else:
            current_batch.append(p_text)
            current_para_refs.append(p_num)
            current_len += len(p_text) + 2

    if current_batch:
        chunk_str = "\n\n".join(current_batch)
        word_count = len(chunk_str.split())
        ref = (
            f"Paragraph {current_para_refs[0]}"
            if len(current_para_refs) == 1
            else f"Paragraphs {current_para_refs[0]}-{current_para_refs[-1]}"
        )
        all_chunks.append({
            "contract_id": contract_id,
            "organization_id": organization_id,
            "chunk_index": chunk_index,
            "content": chunk_str,
            "token_count": word_count,
            "page_number": None,
            "embedding_metadata": {
                "source_type": "docx",
                "reference": ref,
                "paragraph_range": current_para_refs,
                "char_count": len(chunk_str),
                "word_count": word_count,
            },
        })
        chunk_index += 1

    # Chunk table contents
    if tables_data:
        table_lines = [f"[{ref}]: {txt}" for ref, txt in tables_data]
        table_chunks = _split_into_chunks("\n".join(table_lines), max_chars=1000)
        for tc in table_chunks:
            word_count = len(tc.split())
            all_chunks.append({
                "contract_id": contract_id,
                "organization_id": organization_id,
                "chunk_index": chunk_index,
                "content": tc,
                "token_count": word_count,
                "page_number": None,
                "embedding_metadata": {
                    "source_type": "docx",
                    "reference": "Tables",
                    "char_count": len(tc),
                    "word_count": word_count,
                },
            })
            chunk_index += 1

    metadata = {
        "source_type": "docx",
        "paragraph_count": len(doc.paragraphs),
        "table_count": len(doc.tables),
        "total_characters": total_text_length,
        "total_chunks": len(all_chunks),
    }

    return all_chunks, metadata


def save_upload_file(
    content: bytes,
    extension: str,
    organization_id: uuid.UUID,
) -> Tuple[Path, str]:
    """
    Save uploaded bytes to a secure path on disk inside settings.UPLOAD_DIR.
    Uses UUID filename to eliminate path traversal vulnerabilities.
    Returns: (absolute_file_path, safe_random_filename).
    """
    upload_root = Path(settings.UPLOAD_DIR)
    org_folder = upload_root / str(organization_id)
    org_folder.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}{extension}"
    target_path = org_folder / safe_filename

    target_path.write_bytes(content)
    return target_path, safe_filename


def compute_file_hash(content: bytes) -> str:
    """
    Compute SHA-256 hash of file content.
    """
    return hashlib.sha256(content).hexdigest()
