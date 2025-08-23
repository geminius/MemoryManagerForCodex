from __future__ import annotations

from codex.memory import redact


def test_redact_filters_sensitive_strings() -> None:
    text = (
        "Email a@b.com with key sk-1234567890ABCDEF and token ABCDEFGHIJKLMNOPQRSTUV"
    )
    redacted = redact(text)
    assert "a@b.com" not in redacted
    assert "sk-1234567890ABCDEF" not in redacted
    assert "ABCDEFGHIJKLMNOPQRSTUV" not in redacted
    assert "<redacted:email>" in redacted
    assert "<redacted:api_key>" in redacted
    assert "<redacted:secret>" in redacted
