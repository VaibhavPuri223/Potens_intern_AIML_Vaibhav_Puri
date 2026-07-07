from src.tools import normalize_text


def test_normalize_text():
    assert normalize_text("  Hello World  ") == "hello world"
