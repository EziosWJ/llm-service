from src.services.chunker import chunk_text


def test_split_by_paragraphs():
    text = "第一段 内容。\n\n第二段 内容。"

    chunks = chunk_text(text, chunk_size=512, overlap=50)

    assert len(chunks) == 2
    assert chunks[0].text == "第一段 内容。"
    assert chunks[1].text == "第二段 内容。"
    assert chunks[0].metadata["paragraph_index"] == 0
    assert chunks[1].metadata["paragraph_index"] == 1


def test_long_paragraph_secondary_split_with_overlap():
    text = "abcdefghijkl"

    chunks = chunk_text(text, chunk_size=5, overlap=2)

    assert len(chunks) == 4
    assert chunks[0].text == "abcde"
    assert chunks[1].text == "defgh"
    assert chunks[2].text == "ghijk"
    assert chunks[3].text == "jkl"
    assert chunks[0].metadata["subchunk_index"] == 0
    assert chunks[3].metadata["subchunk_index"] == 3


def test_chunk_metadata_passthrough():
    text = "alpha beta"
    chunks = chunk_text(text, metadata={"doc_id": "d1"})

    assert len(chunks) == 1
    assert chunks[0].metadata["doc_id"] == "d1"


def test_invalid_overlap():
    text = "some text"

    try:
        chunk_text(text, chunk_size=4, overlap=4)
        assert False, "should raise ValueError"
    except ValueError as e:
        assert "overlap must be < chunk_size" in str(e)
