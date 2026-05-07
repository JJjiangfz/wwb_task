import json

from eval_pipeline.trace import normalize_messages, save_trace


def test_normalize_messages_preserves_openai_roles():
    messages, warning = normalize_messages(
        [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "tool", "content": "result"},
        ],
        "fallback user",
        "fallback assistant",
    )

    assert warning is None
    assert [message["role"] for message in messages] == ["system", "user", "assistant", "tool"]


def test_normalize_messages_falls_back_when_empty():
    messages, warning = normalize_messages([], "do it", "done")

    assert warning
    assert messages == [
        {"role": "user", "content": "do it"},
        {"role": "assistant", "content": "done"},
    ]


def test_save_trace_writes_indented_json(tmp_path):
    path = tmp_path / "trace.json"
    save_trace(path, [{"role": "user", "content": "hi"}])

    text = path.read_text(encoding="utf-8")
    assert "\n    " in text
    assert json.loads(text)[0]["role"] == "user"
