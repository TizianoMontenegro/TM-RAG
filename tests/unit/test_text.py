from app.utils.text import clean_query, truncate_context


def test_clean_query_strips_whitespace():
    assert clean_query("   hello world   ") == "hello world"


def test_clean_query_collapses_internal_whitespace():
    assert clean_query("hello    world\n\n\ntest") == "hello world test"


def test_clean_query_removes_null_bytes():
    assert clean_query("hello\x00world") == "helloworld"


def test_truncate_context_below_limit():
    context = "This is a short context."
    assert truncate_context(context, max_tokens=10) == context


def test_truncate_context_at_sentence_boundary():
    # 5 tokens = 20 chars
    # "Sentence 1. Sentence 2." -> 23 chars
    context = "Sentence 1. Sentence 2."
    truncated = truncate_context(context, max_tokens=5)
    assert truncated == "Sentence 1."


def test_truncate_context_fallback():
    # 5 tokens = 20 chars
    # "Thisisalongstringwithoutanysentenceboundary"
    context = "Thisisalongstringwithoutanysentenceboundary"
    truncated = truncate_context(context, max_tokens=5)
    assert truncated == "Thisisalongstringwit"
