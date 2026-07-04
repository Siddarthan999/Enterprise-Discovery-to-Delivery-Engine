def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80):
    """
    Improved chunking:
    - Adds overlap for context continuity
    - Returns structured chunks (not just strings)
    - Preserves indexing for retrieval
    """

    if not text:
        return []

    words = text.split()
    chunks = []

    i = 0
    chunk_index = 0

    while i < len(words):
        end = i + chunk_size
        chunk_words = words[i:end]

        chunk = " ".join(chunk_words)

        chunks.append({
            "content": chunk,
            "index": chunk_index,
            "start_word": i,
            "end_word": min(end, len(words))
        })

        # move with overlap
        i += (chunk_size - overlap)
        chunk_index += 1

    return chunks