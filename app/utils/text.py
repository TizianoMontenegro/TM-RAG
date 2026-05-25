import re


def clean_query(query: str) -> str:
    """Strip leading/trailing whitespace, collapse internal whitespace, remove null bytes."""
    query = query.replace("\x00", "")
    query = re.sub(r"\s+", " ", query)
    return query.strip()


def truncate_context(context: str, max_tokens: int = 3000) -> str:
    """Truncate context string to approximately max_tokens to avoid LLM context overflow.
    Uses character count as a proxy (1 token ≈ 4 chars). Truncates at sentence boundaries
    where possible."""
    max_chars = max_tokens * 4
    if len(context) <= max_chars:
        return context

    truncated = context[:max_chars]

    # Try to find the last sentence boundary before max_chars
    # Sentence boundaries considered: ". ", "! ", "? ", or newline
    matches = list(re.finditer(r"([.!?]\s|\n)", truncated))
    if matches:
        last_match = matches[-1]
        return truncated[: last_match.end()].strip()

    # Fallback: forcefully truncate at max_chars
    return truncated.strip()
