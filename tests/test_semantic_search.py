"""
tests/test_semantic_search.py
-------------------------------
Unit tests for Semantic Desktop Search: indexing, incremental re-index
(unchanged files skipped), and finding files by meaning rather than exact
keyword. Each test uses its own tmp_path as the persist directory so tests
never touch the real index or each other.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.semantic_search import _index_directory_impl, _semantic_search_impl


def test_index_directory_indexes_supported_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text("Machine learning models can be trained on labeled data.")
    (source / "image.png").write_bytes(b"\x89PNG")  # unsupported extension, should be skipped

    store = tmp_path / "store"
    result = _index_directory_impl(str(source), str(store), recursive=True)

    assert "Indexed 1 file(s)" in result


def test_reindex_skips_unchanged_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text("Some content about databases.")

    store = tmp_path / "store"
    _index_directory_impl(str(source), str(store), recursive=True)
    result = _index_directory_impl(str(source), str(store), recursive=True)

    assert "skipped 1 unchanged" in result


def test_semantic_search_finds_relevant_file_by_meaning(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "ml_paper.txt").write_text(
        "This document discusses neural networks, deep learning, and machine "
        "learning model training techniques for image classification."
    )
    (source / "recipe.txt").write_text(
        "To make pasta, boil water, add salt, cook the noodles for ten minutes."
    )

    store = tmp_path / "store"
    _index_directory_impl(str(source), str(store), recursive=True)

    result = _semantic_search_impl("machine learning research", str(store), top_k=1)

    assert "ml_paper.txt" in result
    assert "recipe.txt" not in result


def test_semantic_search_empty_index_says_so(tmp_path):
    store = tmp_path / "store"
    result = _semantic_search_impl("anything", str(store), top_k=5)
    assert "empty" in result.lower()


def test_semantic_search_directory_filter(tmp_path):
    source_a = tmp_path / "a"
    source_a.mkdir()
    (source_a / "doc.txt").write_text("Quarterly financial report and revenue figures.")

    source_b = tmp_path / "b"
    source_b.mkdir()
    (source_b / "doc.txt").write_text("Quarterly financial report and revenue figures.")

    store = tmp_path / "store"
    _index_directory_impl(str(source_a), str(store), recursive=True)
    _index_directory_impl(str(source_b), str(store), recursive=True)

    result = _semantic_search_impl(
        "financial report", str(store), top_k=5, directory_filter=str(source_a)
    )

    assert str(source_a) in result
    assert str(source_b) not in result
