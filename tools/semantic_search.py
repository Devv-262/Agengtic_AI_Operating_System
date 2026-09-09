"""
tools/semantic_search.py
-------------------------
Role: Semantic Desktop Search. index_directory walks a directory, extracts
text from supported files (reusing tools/document_reader.extract_text),
and stores each file's content in a local persisted ChromaDB collection.
semantic_search then finds files by meaning rather than exact keyword
match, using the same collection.

Embeddings are computed locally via ChromaDB's bundled ONNX MiniLM model —
no LLM API call and no API key needed to index or search, so this keeps
working even if NIM/OpenRouter are both unavailable. Re-indexing skips
files whose mtime hasn't changed since the last index (incremental).

Implementation is split into plain functions (_index_directory_impl /
_semantic_search_impl) that take an explicit persist_directory, and thin
@tool wrappers that default it to config.VECTOR_STORE_DIR — this lets tests
point at a temp directory without touching the real index.
"""
import os
from pathlib import Path

from langchain_core.tools import tool

from src.config import VECTOR_STORE_DIR, SEMANTIC_INDEX_MAX_CHARS
from tools._safety import check_path_allowed
from tools.document_reader import extract_text, SUPPORTED_EXTENSIONS

_COLLECTION_NAME = "desktop_files"
_clients: dict = {}  # persist_directory -> chromadb client, cached


def _get_collection(persist_directory: str):
    import chromadb
    from chromadb.utils import embedding_functions

    if persist_directory not in _clients:
        os.makedirs(persist_directory, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_directory)
        _clients[persist_directory] = client
    else:
        client = _clients[persist_directory]

    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )


def _index_directory_impl(directory_path: str, persist_directory: str, recursive: bool) -> str:
    directory = Path(directory_path).expanduser().resolve()
    sandbox_error = check_path_allowed(directory)
    if sandbox_error:
        return sandbox_error
    if not directory.is_dir():
        return f"Error: '{directory}' is not a directory."

    collection = _get_collection(persist_directory)

    walker = os.walk(directory) if recursive else [(str(directory), [], os.listdir(directory))]

    indexed, skipped, failed = 0, 0, 0
    for root, _dirs, filenames in walker:
        for name in filenames:
            path = Path(root) / name
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            file_id = str(path)
            mtime = str(path.stat().st_mtime)

            existing = collection.get(ids=[file_id], include=["metadatas"])
            if existing["ids"] and existing["metadatas"][0].get("mtime") == mtime:
                skipped += 1
                continue

            text = extract_text(path)
            if text.startswith("Error:"):
                failed += 1
                continue

            collection.upsert(
                ids=[file_id],
                documents=[text[:SEMANTIC_INDEX_MAX_CHARS]],
                metadatas=[{"path": file_id, "name": path.name, "mtime": mtime}],
            )
            indexed += 1

    return (
        f"Indexed {indexed} file(s), skipped {skipped} unchanged, "
        f"{failed} failed to extract text, from '{directory}'."
    )


def _semantic_search_impl(query: str, persist_directory: str, top_k: int, directory_filter: str = None) -> str:
    collection = _get_collection(persist_directory)
    total = collection.count()
    if total == 0:
        return "The semantic index is empty — run index_directory on a folder first."

    if directory_filter:
        prefix = str(Path(directory_filter).expanduser().resolve())
        # Chroma has no "starts with" filter; fetch broadly and filter in Python.
        results = collection.query(query_texts=[query], n_results=min(max(top_k * 5, top_k), total))
        rows = list(zip(results["ids"][0], results["metadatas"][0], results["documents"][0], results["distances"][0]))
        rows = [r for r in rows if r[1]["path"].startswith(prefix)][:top_k]
    else:
        results = collection.query(query_texts=[query], n_results=min(top_k, total))
        rows = list(zip(results["ids"][0], results["metadatas"][0], results["documents"][0], results["distances"][0]))

    if not rows:
        return "No matching files found."

    lines = []
    for _id, metadata, document, distance in rows:
        snippet = document[:200].replace("\n", " ")
        lines.append(f"- {metadata['path']} (relevance score: {1 - distance:.2f})\n  \"{snippet}...\"")
    return "\n".join(lines)


@tool
def index_directory(directory_path: str, recursive: bool = True) -> str:
    """
    Indexes text/PDF/DOCX files in a directory for semantic search, storing
    their content in a local vector index. Re-run to pick up new/changed
    files — unchanged files are skipped automatically. Run this before using
    semantic_search on a directory you haven't indexed yet.
    """
    try:
        return _index_directory_impl(directory_path, VECTOR_STORE_DIR, recursive)
    except Exception as e:
        return f"Error indexing directory: {str(e)}"


@tool
def semantic_search(query: str, top_k: int = 5, directory_filter: str = None) -> str:
    """
    Finds files by meaning rather than exact keyword match (e.g. "the PDF
    about machine learning I downloaded last week"). Searches whatever has
    already been indexed via index_directory — if nothing's indexed yet,
    say so and suggest indexing the relevant folder first. Optionally pass
    directory_filter to restrict results to files under a specific folder.
    """
    try:
        return _semantic_search_impl(query, VECTOR_STORE_DIR, top_k, directory_filter)
    except Exception as e:
        return f"Error searching: {str(e)}"


semantic_search_tools = [index_directory, semantic_search]
